/* Rasterize selected SVG outputs offline; no browser or original-site request. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.join(__dirname,'..'),out=process.argv[2],sharp=require(path.join(process.argv[3],'sharp'));
if(!out)throw Error('Output directory required');fs.mkdirSync(out,{recursive:true});
const ctx=vm.createContext({window:{},console});for(const n of ['charts','analysis-charts','network-views'])vm.runInContext(fs.readFileSync(path.join(root,'docs',n+'.js'),'utf8'),ctx);
const data=n=>JSON.parse(fs.readFileSync(path.join(root,'docs/data',n+'.json'),'utf8')),A=ctx.window.AnalysisCharts,G=ctx.window.NetworkViews;
const styles='<style>.axis{fill:#506d80;font-size:12px}.grid-line{stroke:#dce6ec;stroke-width:1}.reference-line{stroke:#93a8b6;stroke-width:1}.bar-name{fill:#274d66;font-size:13px}</style><rect width="100%" height="100%" fill="white"/>';
const samples={dynamics:A.surface(data('dynamics').sections[0].surface),risk:A.line(data('dynamics').sections[0].charts[0]),candles:A.candles(data('watch').sections[0]),forecast:A.forecast(data('ml').sections[0]),growth:A.scatter3d(data('growth').sections[0]),globe:G.sphere(data('globe').sections[0],data('coastlines').arcs),network:G.graph(data('aragorn').sections[0])};
samples.pead=A.scatter(data('strategies').sections.find(s=>s.group==='PEAD'&&s.type==='scatter'));
samples.reflex_hologram=A.hologram(data('regime').sections.find(s=>s.type==='hologram'));
samples.reflex_radar=A.radar(data('regime').sections.find(s=>s.type==='hologram'));
samples.pm_rates=A.line(data('pm_weekend').sections.find(s=>s.title==='미국 금리 분해 · 10Y'));
samples.pm_cta=A.line(data('pm_weekend').sections.find(s=>s.title==='CTA 시스템 추세 · 누적 자산배수'));
samples.gamma_profile=A.optionProfile(data('risk').sections.find(s=>s.type==='optionprofile'&&s.mode==='gamma'));
samples.oi_profile=A.optionProfile(data('risk').sections.find(s=>s.type==='optionprofile'&&s.mode==='oi'));
samples.cftc=A.line(data('risk').sections.find(s=>s.group==='CFTC 포지션'&&s.type==='line'));
samples.news_regions=G.sphere(data('geoecon').sections.find(s=>s.type==='globe'),data('coastlines').arcs);
samples.scenario=ctx.window.ResearchCharts.bars(data('dragonglass').sections.find(s=>s.type==='scenario').rows.filter(r=>r.market==='KR').map(r=>({name:r.name,value:r.beta*-10})),{unit:'%',title:'시장 −10% 가정 · Beta 민감도'});
(async()=>{for(const [name,html] of Object.entries(samples)){let s=html.match(/<svg[\s\S]*<\/svg>/)?.[0];if(!s)throw Error(name+' empty');s=s.replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" font-family="Malgun Gothic, sans-serif" ').replace(/(<svg[^>]*>)/,'$1'+styles);fs.writeFileSync(path.join(out,name+'.svg'),s);await sharp(Buffer.from(s)).resize({width:1100}).png().toFile(path.join(out,name+'.png'));}console.log('Rasterized',Object.keys(samples).length,'chart samples without a browser.');})().catch(e=>{console.error(e);process.exitCode=1;});
