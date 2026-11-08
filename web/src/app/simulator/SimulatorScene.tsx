"use client";

import { useEffect, useRef } from "react";

export type Visibility = Record<string, boolean>;

type Config = {
  case: string;
  side: "R" | "L";
  hip_local: [number, number, number];
  ankle_local: [number, number, number];
  hinge_local: [number, number, number];
  medial_edge_local: [number, number, number];
  plateau_medial_local: [number, number, number];
  plateau_lateral_local: [number, number, number];
  cut_plane_z_local: number;
  tibia_width_at_cut_mm: number;
  pre_hka_deg: number;
  pre_mpta_deg: number;
};

export default function SimulatorScene({
  theta,
  side,
  config,
  opacity,
  visible,
}: {
  theta: number;
  side: "R" | "L";
  config: Config;
  opacity: number;
  visible: Visibility;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const updaterRef = useRef<((theta: number) => void) | null>(null);
  const objectsRef = useRef<Record<string, any>>({});
  const boneMatRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;
    let cleanup: (() => void) | null = null;

    (async () => {
      try {
        const THREE = await import("three");
        const { STLLoader } = await import("three/examples/jsm/loaders/STLLoader.js");
        const { OrbitControls } = await import("three/examples/jsm/controls/OrbitControls.js");
        if (cancelled || !containerRef.current) return;

        const container = containerRef.current;
        const W = container.clientWidth;
        const H = container.clientHeight;

        const scene = new THREE.Scene();

        const camera = new THREE.PerspectiveCamera(45, W / H, 1, 5000);
        camera.position.set(500, -1400, 200);
        camera.up.set(0, 0, 1);
        camera.lookAt(0, 0, 30);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setClearColor(0x000000, 0);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(W, H);
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        container.appendChild(renderer.domElement);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.target.set(0, 0, 30);
        controls.enableDamping = true;
        controls.dampingFactor = 0.08;
        controls.minDistance = 400;
        controls.maxDistance = 3000;

        scene.add(new THREE.AmbientLight(0xffffff, 0.55));
        const key = new THREE.DirectionalLight(0xffffff, 1.0);
        key.position.set(300, -300, 500);
        scene.add(key);
        const rim = new THREE.DirectionalLight(0x88bbff, 0.45);
        rim.position.set(-300, 300, -300);
        scene.add(rim);

        const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
        const loader = new STLLoader();
        const loadSTL = (url: string) =>
          new Promise<any>((resolve, reject) => loader.load(url, resolve, undefined, reject));

        const boneMat = new THREE.MeshStandardMaterial({
          color: 0xd4c9b0,
          metalness: 0.05,
          roughness: 0.78,
          flatShading: false,
          transparent: false,
          opacity: 1,
        });
        boneMatRef.current = boneMat;

        let femurGeo, proxGeo, distGeo;
        try {
          [femurGeo, proxGeo, distGeo] = await Promise.all([
            loadSTL(`${base}/simulator/femur.stl`),
            loadSTL(`${base}/simulator/tibia_proximal.stl`),
            loadSTL(`${base}/simulator/tibia_distal.stl`),
          ]);
        } catch (e) {
          const err = document.createElement("div");
          err.style.cssText =
            "position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:rgba(255,214,140,.9);font:13px ui-monospace,Menlo,monospace;padding:16px;border:1px solid rgba(255,214,140,.3);border-radius:8px;background:rgba(255,214,140,.05)";
          err.textContent = "Failed to load 3D geometry.";
          container.appendChild(err);
          return;
        }
        if (cancelled) return;

        const femurMesh = new THREE.Mesh(femurGeo, boneMat);
        const proxMesh = new THREE.Mesh(proxGeo, boneMat);
        scene.add(femurMesh);
        scene.add(proxMesh);
        objectsRef.current.femur = femurMesh;
        objectsRef.current.tibiaProximal = proxMesh;

        const [hx, hy, hz] = config.hinge_local;
        const pivot = new THREE.Group();
        pivot.position.set(hx, hy, hz);
        const distal = new THREE.Mesh(distGeo, boneMat);
        distal.position.set(-hx, -hy, -hz);
        pivot.add(distal);
        scene.add(pivot);
        objectsRef.current.tibiaDistal = distal;

        // Landmarks
        const landmarks = new THREE.Group();
        const mk = (pt: number[], color: number) => {
          const m = new THREE.Mesh(
            new THREE.SphereGeometry(6, 16, 16),
            new THREE.MeshBasicMaterial({ color })
          );
          m.position.set(pt[0], pt[1], pt[2]);
          landmarks.add(m);
        };
        mk(config.hip_local, 0x4da3ff);
        mk([0, 0, 0], 0xffaa55);
        mk(config.ankle_local, 0x4da3ff);
        mk(config.hinge_local, 0x10b981);
        scene.add(landmarks);
        objectsRef.current.landmarks = landmarks;

        // Femoral axis
        const femAxis = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(...config.hip_local),
            new THREE.Vector3(0, 0, 0),
          ]),
          new THREE.LineBasicMaterial({ color: 0x4da3ff })
        );
        scene.add(femAxis);
        objectsRef.current.femoralAxis = femAxis;

        // Femoral extension (dashed)
        const hipDir = new THREE.Vector3(...config.hip_local).normalize();
        const extEnd = hipDir.clone().multiplyScalar(-650);
        const extLine = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), extEnd]),
          new THREE.LineDashedMaterial({
            color: 0x4da3ff,
            dashSize: 12,
            gapSize: 10,
            transparent: true,
            opacity: 0.6,
          })
        );
        extLine.computeLineDistances();
        scene.add(extLine);
        objectsRef.current.femoralExtension = extLine;

        // Joint line
        const jointLine = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(...config.plateau_medial_local),
            new THREE.Vector3(...config.plateau_lateral_local),
          ]),
          new THREE.LineBasicMaterial({ color: 0x10b981 })
        );
        scene.add(jointLine);
        objectsRef.current.jointLine = jointLine;

        // Tibial axis
        const tibGeom = new THREE.BufferGeometry();
        tibGeom.setAttribute("position", new THREE.BufferAttribute(new Float32Array(6), 3));
        const tibAxis = new THREE.Line(tibGeom, new THREE.LineBasicMaterial({ color: 0x10b981 }));
        scene.add(tibAxis);
        objectsRef.current.tibialAxis = tibAxis;

        // Arcs
        const hkaArc = new THREE.Line(
          new THREE.BufferGeometry(),
          new THREE.LineBasicMaterial({ color: 0xffaa55 })
        );
        scene.add(hkaArc);
        objectsRef.current.hkaArc = hkaArc;

        const mptaArc = new THREE.Line(
          new THREE.BufferGeometry(),
          new THREE.LineBasicMaterial({ color: 0x4da3ff })
        );
        scene.add(mptaArc);
        objectsRef.current.mptaArc = mptaArc;

        // Wedge
        const wedgeGeom = new THREE.BufferGeometry();
        wedgeGeom.setAttribute("position", new THREE.BufferAttribute(new Float32Array(9), 3));
        const wedge = new THREE.Mesh(
          wedgeGeom,
          new THREE.MeshBasicMaterial({
            color: 0xff7733,
            transparent: true,
            opacity: 0.55,
            side: THREE.DoubleSide,
            depthWrite: false,
          })
        );
        scene.add(wedge);
        objectsRef.current.wedge = wedge;

        const slerpVectors = (a: any, b: any, t: number) => {
          const dot = Math.min(1, Math.max(-1, a.dot(b)));
          const omega = Math.acos(dot);
          if (omega < 1e-4) return a.clone().lerp(b, t).normalize();
          const s = Math.sin(omega);
          const c1 = Math.sin((1 - t) * omega) / s;
          const c2 = Math.sin(t * omega) / s;
          return a.clone().multiplyScalar(c1).add(b.clone().multiplyScalar(c2));
        };

        const buildArc = (from: any, to: any, radius: number, segments: number) => {
          const pts: any[] = [];
          for (let i = 0; i <= segments; i++) {
            const v = slerpVectors(from, to, i / segments).multiplyScalar(radius);
            pts.push(v);
          }
          return pts;
        };

        const update = (th: number) => {
          const sign = side === "R" ? 1 : -1;
          const ang = (sign * th * Math.PI) / 180;
          pivot.rotation.y = ang;

          const ca = Math.cos(ang);
          const sa = Math.sin(ang);
          const h = new THREE.Vector3(hx, hy, hz);
          const ankleRel = new THREE.Vector3(...config.ankle_local).sub(h);
          const ankleNew = h
            .clone()
            .add(
              new THREE.Vector3(
                ankleRel.x * ca + ankleRel.z * sa,
                ankleRel.y,
                -ankleRel.x * sa + ankleRel.z * ca
              )
            );

          const tp = tibAxis.geometry.attributes.position as any;
          tp.setXYZ(0, 0, 0, 0);
          tp.setXYZ(1, ankleNew.x, ankleNew.y, ankleNew.z);
          tp.needsUpdate = true;

          const femExt = hipDir.clone().negate();
          const tibDir = ankleNew.clone().normalize();
          hkaArc.geometry.dispose();
          hkaArc.geometry = new THREE.BufferGeometry().setFromPoints(
            buildArc(femExt, tibDir, 90, 30)
          );

          const tibUp = tibDir.clone().negate();
          const jlDir = new THREE.Vector3(...config.plateau_medial_local)
            .sub(new THREE.Vector3(...config.plateau_lateral_local))
            .normalize();
          mptaArc.geometry.dispose();
          mptaArc.geometry = new THREE.BufferGeometry().setFromPoints(
            buildArc(tibUp, jlDir, 45, 40)
          );

          const proxMedial = new THREE.Vector3(...config.medial_edge_local);
          const pmRel = proxMedial.clone().sub(h);
          const distalMedial = h
            .clone()
            .add(
              new THREE.Vector3(
                pmRel.x * ca + pmRel.z * sa,
                pmRel.y,
                -pmRel.x * sa + pmRel.z * ca
              )
            );
          const wp = wedge.geometry.attributes.position as any;
          wp.setXYZ(0, h.x, h.y, h.z);
          wp.setXYZ(1, proxMedial.x, proxMedial.y, proxMedial.z);
          wp.setXYZ(2, distalMedial.x, distalMedial.y, distalMedial.z);
          wp.needsUpdate = true;
        };

        update(theta);
        updaterRef.current = update;

        let frameId = 0;
        const animate = () => {
          frameId = requestAnimationFrame(animate);
          controls.update();
          renderer.render(scene, camera);
        };
        animate();

        const ro = new ResizeObserver(() => {
          const w = container.clientWidth;
          const h = container.clientHeight;
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);
        });
        ro.observe(container);

        cleanup = () => {
          ro.disconnect();
          cancelAnimationFrame(frameId);
          controls.dispose();
          renderer.dispose();
          femurGeo.dispose();
          proxGeo.dispose();
          distGeo.dispose();
          boneMat.dispose();
          if (container.contains(renderer.domElement)) {
            container.removeChild(renderer.domElement);
          }
        };
      } catch (err) {
        console.error("[simulator] scene setup failed", err);
      }
    })();

    return () => {
      cancelled = true;
      if (cleanup) cleanup();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config]);

  useEffect(() => {
    updaterRef.current?.(theta);
  }, [theta]);

  useEffect(() => {
    if (boneMatRef.current) {
      boneMatRef.current.opacity = opacity;
      boneMatRef.current.transparent = opacity < 0.99;
      boneMatRef.current.needsUpdate = true;
    }
  }, [opacity]);

  useEffect(() => {
    Object.entries(visible).forEach(([key, val]) => {
      const obj = objectsRef.current[key];
      if (obj) obj.visible = val;
    });
  }, [visible]);

  return <div ref={containerRef} style={{ width: "100%", height: "100%" }} />;
}