import path from 'node:path';
import sharp from 'sharp';
const HERE='/Users/robin/Claude/Projects/gr-task-map-fix-late/assets/pilots/map-rebuild-spike/reconcile-late';
const BG={r:26,g:20,b:14}, W=620, H=388, L=28, G=6;
const label=(t,w,c='#e8d5b0')=>Buffer.from(`<svg width="${w}" height="${L}"><rect width="${w}" height="${L}" fill="#1a1409"/><text x="8" y="19" font-family="DejaVu Sans,Helvetica,Arial" font-size="14" fill="${c}">${t.replace(/&/g,'&amp;')}</text></svg>`);
async function cell(f,cap,c){const img=await sharp(f).resize(W,H,{fit:'contain',background:BG}).toBuffer();
 return sharp({create:{width:W,height:H+L,channels:3,background:BG}}).composite([{input:label(cap,W,c),top:0,left:0},{input:img,top:L,left:0}]).png().toBuffer();}
const rows=[];
for(const [id,name] of [['e6-glow-mesa','E6 Glow Mesa'],['e7-relay-valley','E7 Relay Valley']]){
 for(const spot of ['center','north']){
  const cells=await Promise.all([
   cell(path.join(HERE,'shots-before-reweld',`${id}-${spot}.png`),`BEFORE — ${name} (${spot}): painted fallback, state=failed, panorama=off`,'#e59b8a'),
   cell(path.join(HERE,'shots',`${id}-${spot}.png`),`AFTER — ${name} (${spot}): glb, state=ready, own panorama`,'#9ad5a8'),
   cell(path.join('/Users/robin/Claude/Projects/gr-task-map-fix-late/assets/raw',`plate-contract-${id}.png`),`PLATE (promised) — ${id}`,'#f0c987'),
  ]);
  rows.push(await sharp({create:{width:W*3+G*2,height:H+L,channels:3,background:BG}})
   .composite(cells.map((input,i)=>({input,top:0,left:i*(W+G)}))).png().toBuffer());
 }}
await sharp({create:{width:W*3+G*2,height:(H+L)*rows.length+G*(rows.length-1),channels:3,background:BG}})
 .composite(rows.map((input,i)=>({input,top:i*(H+L+G),left:0}))).png().toFile(path.join(HERE,'boards','before-after-recovered.png'));
console.log('boards/before-after-recovered.png');
