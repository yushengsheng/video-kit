import {app} from '../../../scripts/app.js';
import {api} from '../../../scripts/api.js';

app.registerExtension({
  name:'local.handdraw.preview',
  async beforeRegisterNodeDef(nodeType,nodeData) {
    if (!['HanddrawRender','HanddrawVerify'].includes(nodeData.name)) return;
    const created=nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated=function() {
      created?.apply(this,arguments);
      const container=document.createElement('div');
      Object.assign(container.style,{display:'flex',flexDirection:'column',gap:'8px',padding:'8px',overflow:'auto',background:'#20252b',color:'#e2e6eb',fontSize:'13px'});
      const text=document.createElement('div');
      Object.assign(text.style,{whiteSpace:'pre-wrap',overflowWrap:'anywhere'});
      text.textContent='运行后显示结果。';
      container.append(text);
      this.handdrawPanel={container,text};
      this.addDOMWidget('handdraw-result','div',container,{serialize:false,hideOnZoom:false});
      const height=nodeData.name==='HanddrawRender'?410:270;
      this.setSize([440,height]);
    };
    const executed=nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted=function(message) {
      executed?.apply(this,arguments);
      const panel=this.handdrawPanel;
      if (!panel) return;
      panel.text.textContent=(message.text??[]).join('\n');
      panel.container.querySelectorAll('video').forEach(video=>{video.pause();video.remove();});
      if (message.handdraw_video?.[0]) {
        const info=message.handdraw_video[0];
        const video=document.createElement('video');
        video.controls=true;video.preload='metadata';
        video.style.width='100%';video.style.maxHeight='235px';
        video.src=api.apiURL('/view?'+new URLSearchParams(info).toString());
        video.poster=api.apiURL('/view?'+new URLSearchParams({...info,filename:'cover.png'}).toString());
        panel.container.prepend(video);
      }
      this.setDirtyCanvas(true,true);
    };
  },
});
