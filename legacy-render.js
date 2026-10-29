// 历史款 A–F 的编号定位与 4:3 适配（来自最早的独立编辑器）。
// 默认参数输出与历史版本逐像素一致；verify.cjs 会检查，修改前务必理解这一点。
const config={
A1:{name:'漫画-紧凑构图',x:330,y:818,size:112,max:282,mode:'fit'},
B1:{name:'黏土-紧凑构图',x:382,y:818,size:104,max:280,mode:'fit'},
A2:{name:'漫画-安全构图',x:447,y:745,size:88,max:224,mode:'crop'},
B2:{name:'黏土-安全构图',x:505,y:740,size:76,max:200,mode:'crop'}
};
Object.assign(config,{E:{name:'漫画-最初版本',style:'comic',fill:'#fff0bd',x:265,y:792,size:115,max:350,mode:'fit'},F:{name:'黏土-最初版本',x:293,y:790,size:115,max:350,mode:'fit'}});
for(const [key,label] of Object.entries({A1:'A',B1:'B',A2:'C',B2:'D',E:'E',F:'F'})) config[key].label=label;

// opt.href  底图（缩略图时传小图）；opt.layer  'all' | 'base'（无编号）| 'text'（仅编号，透明底）；opt.height 输出像素高度
function svg(k,ratio='16:9',episode='001',opt={}){
const c=config[k],comic=k.startsWith('A')||c.style==='comic',layer=opt.layer||'all',href=opt.href||originals[k],h=opt.height||1080,w=(ratio==='4:3'?1440:1920)*h/1080,n=episode;
const text=layer==='base'?'':'<text class="episode-number" x="'+c.x+'" y="'+c.y+'" text-anchor="middle" dominant-baseline="central" font-family="Arial Black, Arial, sans-serif" font-size="'+(n.length>3?c.size*.82:c.size)+'" font-style="'+(comic?'italic':'normal')+'" font-weight="900" fill="'+(c.fill||(comic?'#ffe52b':'#cd4c1a'))+'" stroke="'+(comic?'#141c22':'#8f3617')+'" stroke-width="'+(comic?1.6:1)+'" paint-order="stroke fill">#'+n+'</text>';
const image=layer==='text'?'':'<image width="1920" height="1080" preserveAspectRatio="none" href="'+href+'"/>';
const content=image+'<g id="episode-layer" transform="scale('+(1920/1672)+' '+(1080/941)+')">'+text+'</g>';
let body=content,box='0 0 1920 1080';
if(ratio==='4:3'&&c.mode==='crop')box='240 0 1440 1080';
if(ratio==='4:3'&&c.mode==='fit'){box='0 0 1440 1080';body=(layer==='text'?'':'<defs><filter id="soft"><feGaussianBlur stdDeviation="24"/></filter></defs><image x="-40" y="-40" width="1520" height="1160" preserveAspectRatio="xMidYMid slice" href="'+href+'" filter="url(#soft)"/><rect width="1440" height="1080" fill="#0e1718" opacity=".22"/>')+'<g transform="translate(0 135) scale(.75)">'+content+'</g>'}
return '<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="'+box+'"><title>'+c.name+' #'+n+' '+ratio+'</title>'+body+'</svg>'
}
