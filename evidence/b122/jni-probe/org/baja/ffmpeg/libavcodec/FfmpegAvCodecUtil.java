package org.baja.ffmpeg.libavcodec;

/** B122 probe stub: declares ONLY native signatures (JNI symbol names depend on this exact class name). No vendor code. */
public class FfmpegAvCodecUtil {
    public static native void av_log_set_level(int level);            // exported as Java_..._av_1log_1set_1level
    public static native int getFfmpegCodecID0(String name);          // exported
    public static native long avcodec_find_decoder(int id);           // exported
    public static native void avcodec_free_context(long h);           // NOT exported (only libavcodec's own avcodec_free_context)
    public static native void av_frame_free(long h);                  // NOT exported
    public static native void av_free(long h);                        // only a C++-mangled ?Java_... export
    public static native int avcodec_close(long h);                   // only a C++-mangled ?Java_... export
}
