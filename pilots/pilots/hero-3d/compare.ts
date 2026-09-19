// Standalone asset-review page, deliberately unreachable from the application entry point.
import * as THREE from 'three';
import { createGltfLoader } from '../../../src/assets/AssetLoading';
import { Hero } from '../../../src/entities/Hero';
import { markStartupFrameReady } from '../../../src/assets/generated';
import { spriteAnimationDiagnostics } from '../../../src/assets/SpriteAnimator';
import { assetSlots } from '../../../src/assets/slots';
import type { Intents } from '../../../src/core/InputController';

const canvas = document.querySelector<HTMLCanvasElement>('canvas')!;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setSize(600, 480); renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1;
const scene = new THREE.Scene(); scene.background = new THREE.Color('#e6d9bc');
scene.add(new THREE.HemisphereLight('#fff4dc', '#8c785c', 2));
const key = new THREE.DirectionalLight('#fff7e5', 2.2); key.position.set(-3,6,5); scene.add(key);
const fill = new THREE.DirectionalLight('#dcecf0', .7); fill.position.set(4,3,-3); scene.add(fill);
const camera = new THREE.OrthographicCamera(-1.65,1.65,1.32,-1.32,.1,100);
camera.position.set(0,6.3,6); camera.lookAt(0,.9,0);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(20,20),new THREE.MeshStandardMaterial({color:'#dcc9a7',roughness:1}));
ground.rotation.x=-Math.PI/2; ground.position.y=-.012; scene.add(ground);
const gltf = await createGltfLoader().loadAsync('./hero-3d.glb');
const pilot = new THREE.Group(); pilot.add(gltf.scene); pilot.position.x=-.77; scene.add(pilot);
gltf.scene.scale.setScalar(.83);
const mixer = new THREE.AnimationMixer(gltf.scene); const clip = gltf.animations[0];
if (!clip) throw new Error('Walk animation missing');
mixer.clipAction(clip).play();
const hero = new Hero(); const spriteRoot=new THREE.Group(); spriteRoot.position.x=.77; spriteRoot.add(hero.group); scene.add(spriteRoot);
markStartupFrameReady();
const terrain = { bounds:{minX:-100,maxX:100,minZ:-100,maxZ:100}, sample:()=>({zone:'bank' as const,walkable:true,speedMul:1}) };
const intents = {move:new THREE.Vector2(),confirm:false,upgrade:false,rotateBuild:false,weaponToggle:false,build:false,cancel:false,buildSlot:null,restart:false,pause:false,mute:false,debugSpawn:false,debugXp:false,debugPlant:false} satisfies Intents;
const headings=['s','se','e','ne','n','nw','w','sw'];
let heading='s';
function step(dt:number) { hero.update(dt,intents,terrain); hero.group.position.set(0,0,0); hero.snapRenderState(); }
function setDirection(direction:string) {
  const angle=headings.indexOf(direction)*Math.PI/4;
  heading=direction; intents.move.set(Math.sin(angle),Math.cos(angle));
  pilot.rotation.y=angle+Math.PI;
  hero.resetRun(new THREE.Vector3());
  for(let i=0;i<120;i++) step(1/60);
}
setDirection('s');
for(let tries=0;tries<1200;tries++) {
  step(1/60); renderer.render(scene,camera);
  const snap=spriteAnimationDiagnostics()[assetSlots.charHero];
  if(snap?.loaded && snap.clip==='walk' && snap.frameCount>1) break;
  await new Promise(resolve=>setTimeout(resolve,50));
  if(tries===1199) throw new Error('Current sprite walk did not become ready');
}
const api = {
  async pose(direction:string,phase:number) {
    if (!headings.includes(direction)) throw new Error('Unknown heading');
    setDirection(direction);
    // Use Hero.update and the runtime animator's real ground-distance clock. Select a
    // cycle phase by stepping it, never substituting a sheet or forcing a frame index.
    let snap=spriteAnimationDiagnostics()[assetSlots.charHero]!;
    for(let i=0;i<2400;i++) {
      const previousPhase=snap.motionPhase??0;
      step(1/600); snap=spriteAnimationDiagnostics()[assetSlots.charHero]!;
      const p=snap.motionPhase??0;
      if(phase===0 ? p<previousPhase : previousPhase<phase && p>=phase) break;
      if(i===2399) throw new Error(`No phase ${phase} for ${direction}`);
    }
    if(snap.direction!==direction || snap.mirrored || !snap.loaded) throw new Error(`Wrong sprite orientation: ${JSON.stringify(snap)}`);
    mixer.setTime(phase*clip.duration); scene.updateMatrixWorld(true); renderer.render(scene,camera);
    const bones: Record<string, number[]> = {};
    gltf.scene.traverse(object=>{if((object as THREE.Bone).isBone) bones[object.name]=object.getWorldPosition(new THREE.Vector3()).toArray();});
    return {direction,phase,clip:clip.name,duration:clip.duration,sprite:{...snap,motionPhase:snap.motionPhase,sourceFrameKey:snap.sourceFrameKey},bones};
  },
  dataURL:()=>canvas.toDataURL('image/png'),
};
(window as unknown as {heroPilot:typeof api}).heroPilot=api;
await api.pose('s',0); document.querySelector('#status')!.textContent='Ready · pilot only';
let playing=false,previous=0;
function animate(now:number){if(!playing)return; const dt=Math.min(.05,(now-previous)/1000); previous=now; step(dt); mixer.update(dt); renderer.render(scene,camera); requestAnimationFrame(animate);}
document.querySelector('#play')!.addEventListener('click',()=>{playing=!playing;document.querySelector('#play')!.textContent=playing?'Pause walk':'Play walk';if(playing){previous=performance.now();requestAnimationFrame(animate);}});
document.querySelector('#heading')!.addEventListener('change',event=>{setDirection((event.target as HTMLSelectElement).value);if(!playing) void api.pose(heading,0);});
