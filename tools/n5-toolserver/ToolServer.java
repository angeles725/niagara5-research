import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.PrintStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.util.spi.ToolProvider;

/**
 * Persistent in-process javac/javap runner for tools/n5-fidelity.py (--tool-server).
 *
 * Launched as `java ToolServer.java` (source-launch mode). Speaks a binary,
 * length-prefixed protocol over stdin/stdout so arbitrary paths and diagnostic
 * text (any bytes, newlines included) round-trip safely:
 *
 *   handshake (server -> client, once, after startup): the single byte 'R'
 *   request  (client -> server): int32 argc (>=1), then argc x [int32 len, UTF-8 bytes];
 *            arg 0 is the tool name ("javac" | "javap"), the rest are its arguments
 *   response (server -> client): int32 exit code, int32 len + UTF-8 stdout,
 *            int32 len + UTF-8 stderr
 *
 * Each request gets fresh writers, so nothing leaks between requests. The server
 * exits cleanly on stdin EOF. Real stdout is reserved for the protocol; anything
 * a tool prints to System.out/System.err is redirected to stderr.
 */
public class ToolServer {
    public static void main(String[] args) throws IOException {
        DataOutputStream out = new DataOutputStream(new BufferedOutputStream(System.out, 1 << 16));
        System.setOut(new PrintStream(System.err, true, StandardCharsets.UTF_8));
        DataInputStream in = new DataInputStream(new BufferedInputStream(System.in, 1 << 16));
        out.writeByte('R');
        out.flush();
        while (true) {
            int argc;
            try {
                argc = in.readInt();
            } catch (EOFException eof) {
                return;
            }
            String[] req = new String[argc];
            for (int i = 0; i < argc; i++) {
                byte[] b = new byte[in.readInt()];
                in.readFully(b);
                req[i] = new String(b, StandardCharsets.UTF_8);
            }
            int rc;
            StringWriter so = new StringWriter();
            StringWriter se = new StringWriter();
            try (PrintWriter pso = new PrintWriter(so); PrintWriter pse = new PrintWriter(se)) {
                ToolProvider tool = argc == 0 ? null : ToolProvider.findFirst(req[0]).orElse(null);
                if (tool == null) {
                    rc = 127;
                    pse.print("ToolServer: unknown tool " + (argc == 0 ? "<none>" : req[0]) + "\n");
                } else {
                    String[] toolArgs = new String[argc - 1];
                    System.arraycopy(req, 1, toolArgs, 0, argc - 1);
                    try {
                        rc = tool.run(pso, pse, toolArgs);
                    } catch (Throwable t) {
                        rc = 126;
                        pse.print("ToolServer: " + t + "\n");
                    }
                }
            }
            writeBlob(out, rc, so.toString(), se.toString());
        }
    }

    private static void writeBlob(DataOutputStream out, int rc, String stdout, String stderr) throws IOException {
        byte[] o = stdout.getBytes(StandardCharsets.UTF_8);
        byte[] e = stderr.getBytes(StandardCharsets.UTF_8);
        out.writeInt(rc);
        out.writeInt(o.length);
        out.write(o);
        out.writeInt(e.length);
        out.write(e);
        out.flush();
    }
}
