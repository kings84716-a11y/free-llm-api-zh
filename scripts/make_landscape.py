#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_landscape.py — 生成 1920x1080 横屏长视频（B站/YouTube）
含：片头/片尾卡片、AI配音、证据图、BGM混音、底部字幕
"""
import json, os, subprocess, asyncio, sys
import edge_tts

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(BASE, "video")
SHOTS = os.path.join(VIDEO, "shots")
BUILD = os.path.join(VIDEO, "build_h")
os.makedirs(BUILD, exist_ok=True)
W,H,FPS = 1920,1080,30
BGM = os.path.join(VIDEO,"assets","bgm.mp3")

def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode!=0:
        print("FAIL:"," ".join(cmd[:3]),r.stderr[-300:]);sys.exit(1)
    return r

def dur(p):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","default=nw=1:nk=1",p]).stdout.strip())

async def tts(text,out,voice,rate):
    await edge_tts.Communicate(text,voice,rate=rate).save(out)

def ass_ts(s):
    h=int(s//3600);m=int((s%3600)//60);x=s%60
    return f"{h:d}:{m:02d}:{x:05.2f}"

async def main():
    story=sys.argv[1] if len(sys.argv)>1 else "storyboard_landscape.json"
    outname=sys.argv[2] if len(sys.argv)>2 else "free-api-ep1-landscape.mp4"
    sb=json.load(open(os.path.join(VIDEO,story)))
    voice,rate=sb["voice"],sb.get("rate","+0%")
    intro,outro=sb.get("intro"),sb.get("outro")
    segs=[]; timeline=[]; t=0.0

    async def add_card(img, seconds, caption):
        nonlocal t
        seg=os.path.join(BUILD,f"card_{len(segs)}.mp4")
        run(["ffmpeg","-y","-loop","1","-i",os.path.join(SHOTS,img),
             "-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-t",str(seconds),
             "-vf",f"scale={W}:{H},setsar=1","-c:v","libx264","-tune","stillimage",
             "-c:a","aac","-shortest","-r",str(FPS),seg])
        segs.append(seg); timeline.append((t,t+seconds,caption)); t+=seconds

    if intro: await add_card(intro,3.5,"")

    for i,sc in enumerate(sb["scenes"]):
        a=os.path.join(BUILD,f"a{i}.mp3"); await tts(sc["narration"],a,voice,rate)
        d=dur(a); img=os.path.join(SHOTS,sc["shot"]); seg=os.path.join(BUILD,f"s{i}.mp4")
        # 横屏：图等比铺满1080高、居中，深色填充；底部留字幕条
        vf=(f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0d1117,"
            f"drawbox=x=0:y={H-150}:w={W}:h=150:color=0x0d1117@0.7:t=fill,setsar=1[v]")
        run(["ffmpeg","-y","-loop","1","-i",img,"-i",a,"-filter_complex",vf,
             "-map","[v]","-map","1:a","-c:v","libx264","-tune","stillimage",
             "-c:a","aac","-b:a","128k","-pix_fmt","yuv420p","-shortest","-r",str(FPS),seg])
        segs.append(seg); timeline.append((t,t+d,sc["caption"])); t+=d

    if outro: await add_card(outro,4.0,"")

    # concat
    lf=os.path.join(BUILD,"list.txt")
    open(lf,"w").write("".join(f"file '{s}'\n" for s in segs))
    merged=os.path.join(BUILD,"merged.mp4")
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lf,"-c","copy",merged])

    # ASS 字幕（横屏底部安全区）
    ass=os.path.join(BUILD,"sub.ass")
    header=("[Script Info]\nScriptType:v4.00+\nPlayResX:1920\nPlayResY:1080\n\n"
      "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
      "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
      "Alignment, MarginL, MarginR, MarginV, Encoding\n"
      "Style: Def,Noto Sans CJK SC,40,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,3,2,0,2,90,90,48,1\n\n"
      "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lines=[header]
    for st,en,txt in timeline:
        if txt: lines.append(f"Dialogue: 0,{ass_ts(st)},{ass_ts(en)},Def,,0,0,0,,{txt.replace(':','：')}\n")
    open(ass,"w").write("".join(lines))

    subbed=os.path.join(BUILD,"subbed.mp4")
    run(["ffmpeg","-y","-i",merged,"-vf",f"ass={ass}","-c:a","copy",subbed])

    # 混 BGM（人声为主，BGM 音量压到 0.12，无人声段自动淡出）
    out=os.path.join(VIDEO,outname)
    if os.path.exists(BGM):
        run(["ffmpeg","-y","-i",subbed,"-stream_loop","-1","-i",BGM,
             "-filter_complex","[1:a]volume=0.12,afade=t=out:st=60:d=4[bg];"
             "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
             "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","160k","-shortest",out])
    else:
        run(["ffmpeg","-y","-i",subbed,"-c","copy",out])
    print("LANDSCAPE OK:",out,f"{dur(out):.1f}s")

asyncio.run(main())
