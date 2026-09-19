import { chromium } from 'playwright';
import sharp from 'sharp';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
const out = 'artifacts/sol/open-findings';
await mkdir(`${out}/_raw/hero`,{recursive:true});
const browser=await chromium.launch({channel:'chromium'});
const page=await browser.newPage({viewport:{width:1000,height:800},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
const rows=[];const composites=[];
const headings=['s','se','e','ne','n','nw','w','sw'];
try {
  await page.goto('http://127.0.0.1:5301/assets/pilots/hero-3d/compare.html',{waitUntil:'domcontentloaded',timeout:60000});
  await page.waitForFunction(()=>window.heroPilot,null,{timeout:120000});
  console.log('Comparison page ready');
  for (let row=0;row<8;row++) for(let phase=0;phase<8;phase++) {
    const record=await page.evaluate(async([direction,phase])=>{const audit=await window.heroPilot.pose(direction,phase/8);return {audit,png:window.heroPilot.dataURL()};},[headings[row],phase]);
    rows.push(record.audit);
    const png=Buffer.from(record.png.split(',')[1],'base64');
    await writeFile(`${out}/_raw/hero/${headings[row]}-${phase}.png`,png);
    composites.push({input:await sharp(png).resize(300,240).toBuffer(),left:80+phase*300,top:108+row*270});
  }
  const loop0=await page.evaluate(()=>window.heroPilot.pose('s',0));
  if(errors.length) throw new Error(`Console/page errors: ${errors.join('\n')}`);
  const svg=`<svg width="2480" height="2290"><style>text{font-family:Arial,sans-serif;fill:#382d25}</style><text x="24" y="35" font-size="25" font-weight="bold">Hero pilot · all eight headings · one complete walk cycle</text><text x="24" y="62" font-size="17">Each pair: 3D diffuse pilot (left) · current runtime sprite (right). Equal ground plane and nominal height. Runtime remains the sprite.</text>${Array.from({length:8},(_,i)=>`<text x="${130+i*300}" y="94" font-size="16">Phase ${i}/8</text>`).join('')}${headings.map((h,i)=>`<text x="22" y="${230+i*270}" font-size="22" font-weight="bold">${h.toUpperCase()}</text>`).join('')}<text x="24" y="2270" font-size="16">Atlas 1024² · RGBA8 with mipmaps 5.33 MiB · conventional diffuse · no runtime promotion</text></svg>`;
  composites.push({input:Buffer.from(svg),left:0,top:0});
  await sharp({create:{width:2480,height:2290,channels:4,background:'#eee2c9'}}).composite(composites).png().toFile(`${out}/hero-eight-heading-board.png`);
  await writeFile(`${out}/hero-walk-audit.json`,JSON.stringify({errors,rows,loop0,method:'Actual Hero.update / SpriteAnimator ground-distance cycle; GLTFLoader + AnimationMixer; no manual sprite frame or mirror override.'},null,2)+'\n');
  console.log(`Captured ${rows.length} actual sprite/GLB pairs; errors ${errors.length}`);
} catch (error) {
  console.error('Capture errors:', JSON.stringify(errors));
  await writeFile(`${out}/_raw/hero-capture-errors.json`,JSON.stringify({errors,failure:String(error)},null,2));
  throw error;
} finally {await browser.close();}
// Artifact-level contract: inspect the exported GLB and its embedded image.
const bytes=await readFile('assets/pilots/hero-3d/hero-3d.glb');
const jsonLength=bytes.readUInt32LE(12);const gltf=JSON.parse(bytes.subarray(20,20+jsonLength).toString());
const binStart=20+jsonLength+8;const view=gltf.bufferViews[gltf.images[0].bufferView];
const image=await sharp(bytes.subarray(binStart+view.byteOffset,binStart+view.byteOffset+view.byteLength)).metadata();
const material=gltf.materials[0];
if(image.width!==1024||image.height!==1024||material.emissiveTexture||material.emissiveFactor?.some(v=>v!==0)||!material.pbrMetallicRoughness?.baseColorTexture||gltf.skins.length!==1||gltf.animations.length!==1) throw new Error('Exported GLB contract failed');
const vertices=gltf.meshes.flatMap(m=>m.primitives).reduce((sum,p)=>sum+gltf.accessors[p.attributes.POSITION].count,0);
const triangles=gltf.meshes.flatMap(m=>m.primitives).reduce((sum,p)=>sum+gltf.accessors[p.indices].count/3,0);
await writeFile(`${out}/hero-after.json`,JSON.stringify({bytes:bytes.length,vertices,triangles,skins:gltf.skins.length,animations:gltf.animations.length,animationNames:gltf.animations.map(a=>a.name),image:{width:image.width,height:image.height},material,rgba8MipMiB:1024*1024*4*4/3/1024**2},null,2)+'\n');
