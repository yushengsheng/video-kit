"""Install the small local node package and both workflow JSON formats."""
import argparse
import hashlib
import sys
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT/"comfyui/handdraw_video"


def workflow(mode,resolution):
    nodes = [
        {"id":1,"type":"HanddrawLoadStory","pos":[80,220],"size":[430,170],"order":0,"inputs":[],"outputs":[{"name":"文案与画面","type":"HANDDRAW_SOURCE","links":[1],"slot_index":0}],
         "widgets_values":[str(ROOT),"content/handdraw-moon-v1/story.json","content/handdraw-moon-v1/art.json"]},
        {"id":2,"type":"HanddrawNarration","pos":[550,220],"size":[330,130],"order":1,"inputs":[{"name":"source","type":"HANDDRAW_SOURCE","link":1}],
         "outputs":[{"name":"含配音字幕的任务","type":"HANDDRAW_JOB","links":[2],"slot_index":0}],"widgets_values":["缺失时生成配音（联网）"]},
        {"id":3,"type":"HanddrawRender","pos":[920,220],"size":[440,410],"order":2,"inputs":[{"name":"job","type":"HANDDRAW_JOB","link":2}],
         "outputs":[{"name":"已导出视频","type":"HANDDRAW_RENDER","links":[3],"slot_index":0}],"widgets_values":[mode,resolution]},
        {"id":4,"type":"HanddrawVerify","pos":[1400,220],"size":[440,270],"order":3,"inputs":[{"name":"render","type":"HANDDRAW_RENDER","link":3}],
         "outputs":[{"name":"检查报告","type":"STRING","links":None}],"widgets_values":[]},
        {"id":5,"type":"Note","pos":[80,20],"size":[800,160],"order":4,"inputs":[],"outputs":[],"widgets_values":[
            "手绘故事 v1｜文案与画面 → 配音/字幕 → Remotion 渲染 → 技术检查\n首次需生成旁白（联网）；匹配缓存可离线复用，无需本地大模型。\n先运行短预览，再打开完整导出。新故事需要匹配的 story.json 和 art.json；只换文案不会自动重画场景。\n改文案或音色后，选择“缺失时生成配音（联网）”。ComfyUI/output/handdraw 下保存视频、字幕和报告。"]},
    ]
    for node in nodes:
        node.update({"flags":{},"mode":0,"properties":{"Node name for S&R":node["type"]}})
    return {"last_node_id":5,"last_link_id":3,"nodes":nodes,"links":[[1,1,0,2,0,"HANDDRAW_SOURCE"],[2,2,0,3,0,"HANDDRAW_JOB"],[3,3,0,4,0,"HANDDRAW_RENDER"]],
            "groups":[],"config":{},"extra":{"ds":{"scale":.75,"offset":[0,0]}},"version":.4}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(comfy, update=False):
    comfy=comfy.expanduser().resolve()
    if not (comfy/"main.py").is_file() or not (comfy/"custom_nodes").is_dir():
        raise ValueError("找不到 ComfyUI 根目录。")
    node=shutil.which("node")
    if not node:raise ValueError("找不到 Node.js。")
    destination=comfy/"custom_nodes/handdraw_video"
    marker=destination/".video-kit-managed.json"
    previous={}
    if destination.exists():
        if not update or not marker.is_file():
            raise FileExistsError("已有节点不是可直接覆盖的受管安装，已保留："+str(destination))
        previous=json.loads(marker.read_text())
        for name,expected in previous.get("files",{}).items():
            path=destination/name
            if not path.is_file() or digest(path)!=expected:
                raise ValueError("已安装节点有本地修改，停止更新："+str(path))
        for name,expected in previous.get("workflows",{}).items():
            path=Path(name)
            if not path.is_file() or digest(path)!=expected:
                raise ValueError("已安装工作流有本地修改，停止更新："+str(path))
    files={}
    for name,mode,resolution in [("手绘故事-01-短预览","首镜预览","720p"),("手绘故事-02-完整导出","完整视频","1080p")]:
        graph=workflow(mode,resolution)
        api={"1":{"class_type":"HanddrawLoadStory","inputs":{"project_directory":str(ROOT),"story_file":"content/handdraw-moon-v1/story.json","art_file":"content/handdraw-moon-v1/art.json"}},
             "2":{"class_type":"HanddrawNarration","inputs":{"source":["1",0],"speech_mode":"缺失时生成配音（联网）"}},
             "3":{"class_type":"HanddrawRender","inputs":{"job":["2",0],"mode":mode,"resolution":resolution}},
             "4":{"class_type":"HanddrawVerify","inputs":{"render":["3",0]}}}
        files[comfy/"user/default/workflows/手绘故事"/(name+".json")]=graph
        files[ROOT/"comfyui/workflows"/(name+"_api.json")]=api
    # Preflight every destination before writing any node/workflow file.
    for path in files:
        if path.exists() and str(path) not in previous.get("workflows",{}):
            raise FileExistsError("已有未受管工作流，已保留："+str(path))
    for name in ["__init__.py","web/preview.js"]:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(PACKAGE/name,target)
    config=destination/"config.json"
    if not config.exists():config.write_text(json.dumps({"project_directory":str(ROOT),"node_executable":node},ensure_ascii=False,indent=2))
    for path,value in files.items():
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2))
    record={"source":"https://github.com/yushengsheng/video-kit.git","files":{name:digest(destination/name) for name in ["__init__.py","web/preview.js"]},"workflows":{str(path):digest(path) for path in files}}
    marker.write_text(json.dumps(record,ensure_ascii=False,indent=2))
    print(json.dumps({"nodes":str(destination),"updated":update,"restart_comfyui_required":True},ensure_ascii=False))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-directory",type=Path,required=True)
    parser.add_argument("--update",action="store_true")
    args=parser.parse_args()
    install(args.comfy_directory,args.update)
