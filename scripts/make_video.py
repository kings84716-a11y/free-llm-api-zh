#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_video.py — 全自动生成不出镜解说视频
分镜JSON -> edge-tts 配音 -> 网站截图做画面 -> ffmpeg 合成带字幕的 mp4
"""
import json, os, subprocess, asyncio, sys
import edge_tts

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(BASE, "video")
SHOTS = os.path.join(VIDEO, "shots")
BUILD = os.path.join(VIDEO, "build")
os.makedirs(BUILD, exist_ok=True)

W, H, FPS = 1080, 1920, 30  # 竖屏 9:16（抖音/视频号/小红书）
def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("CMD FAIL:", " ".join(cmd[:4]), r.stderr[-400:]); sys.exit(1)
    return r

async def tts(text, out, voice, rate):
    comm = edge_tts.Communicate(text, voice, rate=rate)
    await comm.save(out)

def duration(path):
    r = run(["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=nw=1:nk=1", path])
    return float(r.stdout.strip())

def esc_srt(t):
    return t.replace("'","’").replace(":","：")

def ts(sec):
    h=int(sec//3600); m=int((sec%3600)//60); s=sec%60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".",",")

async def main():
    story = sys.argv[1] if len(sys.argv) > 1 else "storyboard_short.json"
    out_name = sys.argv[2] if len(sys.argv) > 2 else "free-api-ep1-short.mp4"
    sb = json.load(open(os.path.join(VIDEO, story)))
    voice, rate = sb["voice"], sb.get("rate","+0%")
    clips = []
    t = 0.0; srt = []
    for i, sc in enumerate(sb["scenes"]):
        audio = os.path.join(BUILD, f"a{i}.mp3")
        await tts(sc["narration"], audio, voice, rate)
        d = duration(audio)
        img = os.path.join(SHOTS, sc["shot"])
        seg = os.path.join(BUILD, f"seg{i}.mp4")
        if sc.get("landscape"):
            # 横版证据图：放大模糊版铺满做背景 + 清晰原图居中，消除大黑边
            vf = (
                f"[0:v]split=2[bg][fg];"
                f"[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,gblur=sigma=30,eq=brightness=-0.25[bg2];"
                f"[fg]scale=1080:-2[fg2];"
                f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
            )
        else:
            # 竖版榜单图：放上部，底部留黑给字幕
            vf = (
                f"[0:v]scale=1080:1560:force_original_aspect_ratio=decrease,"
                f"pad=1080:1920:0:0:color=0x0d1117,setsar=1[v]"
            )
        run(["ffmpeg","-y","-loop","1","-i",img,"-i",audio,
             "-filter_complex", vf,
             "-map","[v]","-map","1:a","-c:v","libx264","-tune","stillimage",
             "-c:a","aac","-b:a","128k","-pix_fmt","yuv420p","-shortest",
             "-r",str(FPS), seg])
        clips.append(seg)
        srt.append((i+1, t, t+d, sc["caption"]))
        t += d
    # concat
    listfile = os.path.join(BUILD,"list.txt")
    open(listfile,"w").write("".join(f"file '{c}'\n" for c in clips))
    merged = os.path.join(BUILD,"merged.mp4")
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",listfile,"-c","copy",merged])
    # 生成 ASS 字幕（写死底部位置，避免 SRT 默认居中遮挡数据）
    ass_path = os.path.join(BUILD,"sub.ass")
    def ass_ts(sec):
        h=int(sec//3600);m=int((sec%3600)//60);s=sec%60
        return f"{h:d}:{m:02d}:{s:05.2f}"
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Def,Noto Sans CJK SC,46,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,3,2,0,2,70,70,150,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for idx,st,en,txt in srt:
        lines.append(f"Dialogue: 0,{ass_ts(st)},{ass_ts(en)},Def,,0,0,0,,{esc_srt(txt)}\n")
    open(ass_path,"w").write("".join(lines))
    # 烧字幕（ASS 已写死底部安全区，不再用 force_style）
    out = os.path.join(VIDEO, out_name)
    run(["ffmpeg","-y","-i",merged,"-vf",f"ass={ass_path}",
         "-c:a","copy",out])
    print("VIDEO OK:", out, f"{duration(out):.1f}s")

asyncio.run(main())
