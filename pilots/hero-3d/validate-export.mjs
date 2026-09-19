// Verify the exported skin and walk without a browser; textures are irrelevant to vertex math.
import {readFile,writeFile} from 'node:fs/promises';
import * as THREE from 'three';
import {GLTFLoader} from 'three/examples/jsm/loaders/GLTFLoader.js';
const bytes=await readFile(new URL('./hero-3d.glb',import.meta.url));
const loader=new GLTFLoader();
loader.register(()=>({name:'ASTRA_CPU_SKIN_AUDIT',loadTexture:async()=>new THREE.Texture()}));
const gltf=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
if(gltf.animations.length!==1)throw new Error('Expected exactly one walk');
gltf.scene.scale.setScalar(.83);
const mixer=new THREE.AnimationMixer(gltf.scene);mixer.clipAction(gltf.animations[0]).play();
const rows=[];let first=[];let last=[];
for(let phase=0;phase<=128;phase++){
  mixer.setTime(phase/128*gltf.animations[0].duration);gltf.scene.updateMatrixWorld(true);
  const feet={footL:Infinity,footR:Infinity};const pose=[];
  gltf.scene.traverse(mesh=>{
    if(!mesh.isSkinnedMesh)return;
    mesh.skeleton.update();
    const {position,skinIndex,skinWeight}=mesh.geometry.attributes;
    for(let i=0;i<position.count;i++){
      const point=new THREE.Vector3().fromBufferAttribute(position,i);
      mesh.applyBoneTransform(i,point).applyMatrix4(mesh.matrixWorld);pose.push(point.toArray());
      let strongest=0;for(let axis=1;axis<4;axis++)if(skinWeight.getComponent(i,axis)>skinWeight.getComponent(i,strongest))strongest=axis;
      const name=mesh.skeleton.bones[skinIndex.getComponent(i,strongest)].name;
      if(name in feet)feet[name]=Math.min(feet[name],point.y);
    }
  });
  if(!Object.values(feet).every(Number.isFinite))throw new Error('Missing skinned boots');
  rows.push({phase:phase/128,...feet});if(phase===0)first=pose;if(phase===128)last=pose;
}
const lowest=Math.min(...rows.flatMap(r=>[r.footL,r.footR]));
const highestSupport=Math.max(...rows.map(r=>Math.min(r.footL,r.footR)));
const loopMax=Math.max(...first.map((p,i)=>Math.hypot(...p.map((v,axis)=>v-last[i][axis]))));
const report={duration:gltf.animations[0].duration,samples:rows.length,lowest,highestSupport,loopMax,rows,method:'Exported GLB through GLTFLoader/AnimationMixer/applyBoneTransform; image decoding stubbed only for CPU vertex audit.'};
await writeFile('artifacts/sol/open-findings/hero-export-walk-audit.json',JSON.stringify(report,null,2)+'\n');
if(lowest<-.001||highestSupport>.006||loopMax>1e-4)throw new Error(`Exported foot contact/loop failed: ${JSON.stringify({lowest,highestSupport,loopMax})}`);
console.log(JSON.stringify({duration:report.duration,samples:report.samples,lowest,highestSupport,loopMax}));
