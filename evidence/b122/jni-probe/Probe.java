import org.baja.ffmpeg.libavcodec.FfmpegAvCodecUtil;

public class Probe {
    interface Call { Object run() throws Throwable; }

    static void t(String label, Call c) {
        try {
            Object r = c.run();
            System.out.println(label + " -> OK " + (r == null ? "" : r));
        } catch (Throwable e) {
            System.out.println(label + " -> " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    public static void main(String[] a) {
        String dir = a[0];
        for (String n : new String[]{"avutil-60", "swresample-6", "avcodec-62", "avformat-62", "swscale-9", "ffmpeg-wrapper"}) {
            System.load(dir + "\\" + n + ".dll");
            System.out.println("loaded " + n + ".dll");
        }
        t("av_log_set_level(-8)      [exported, control]", () -> { FfmpegAvCodecUtil.av_log_set_level(-8); return null; });
        t("getFfmpegCodecID0(h264)   [exported, control]", () -> FfmpegAvCodecUtil.getFfmpegCodecID0("h264"));
        t("avcodec_find_decoder(27)  [exported, control]", () -> FfmpegAvCodecUtil.avcodec_find_decoder(27) != 0L);
        t("avcodec_free_context(0)   [declared, no Java_ export]", () -> { FfmpegAvCodecUtil.avcodec_free_context(0L); return null; });
        t("av_frame_free(0)          [declared, no Java_ export]", () -> { FfmpegAvCodecUtil.av_frame_free(0L); return null; });
        t("av_free(0)                [only ?Java_ C++-mangled export]", () -> { FfmpegAvCodecUtil.av_free(0L); return null; });
        t("avcodec_close(0)          [only ?Java_ C++-mangled export]", () -> FfmpegAvCodecUtil.avcodec_close(0L));
    }
}
