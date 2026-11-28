import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
const W=540,H=960;
const r=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true}); r.setSize(W,H); r.toneMapping=THREE.ACESFilmicToneMapping; r.shadowMap.enabled=true; document.body.appendChild(r.domElement);
const sc=new THREE.Scene(); sc.background=new THREE.Color('#7ec8ff');
const pm=new THREE.PMREMGenerator(r); sc.environment=pm.fromScene(new RoomEnvironment(),0.04).texture;
const cam=new THREE.PerspectiveCamera(45,W/H,0.1,100); cam.position.set(4,4,8); cam.lookAt(0,1,0);
const sun=new THREE.DirectionalLight('#fff',2.5); sun.position.set(5,10,4); sun.castShadow=true; sc.add(sun);
for(let i=-4;i<=4;i++)for(let j=-4;j<=4;j++){const m=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshStandardMaterial({color:(i+j)%2?'#5bd45b':'#4cc24c',roughness:0.35,metalness:0.05}));m.position.set(i,-0.5,j);m.receiveShadow=true;sc.add(m);}
const g=new THREE.Mesh(new THREE.BoxGeometry(1,1,1),new THREE.MeshStandardMaterial({color:'#ffcc33',metalness:1,roughness:0.2,emissive:'#ff9900',emissiveIntensity:0.4}));g.position.y=0.5;g.castShadow=true;sc.add(g);
const comp=new EffectComposer(r); comp.addPass(new RenderPass(sc,cam)); comp.addPass(new UnrealBloomPass(new THREE.Vector2(W,H),0.6,0.4,0.85)); comp.addPass(new OutputPass());
window.seek=t=>{g.rotation.y=t;comp.render();};
window.engineReady=Promise.resolve(true);
