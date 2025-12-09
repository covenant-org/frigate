import { baseUrl } from "@/api/baseUrl";
import { LivePlayerError, PlayerStatsType } from "@/types/live";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CgSleep } from "react-icons/cg";

type WebRtcPlayerProps = {
  className?: string;
  camera: string;
  playbackEnabled?: boolean;
  audioEnabled?: boolean;
  volume?: number;
  microphoneEnabled?: boolean;
  iOSCompatFullScreen?: boolean; // ios doesn't support fullscreen divs so we must support the video element
  pip?: boolean;
  getStats?: boolean;
  setStats?: (stats: PlayerStatsType) => void;
  onPlaying?: () => void;
  onError?: (error: LivePlayerError) => void;
};

export default function WebRtcPlayer({
  className,
  camera,
  playbackEnabled = true,
  audioEnabled = false,
  volume,
  microphoneEnabled = false,
  iOSCompatFullScreen = false,
  pip = false,
  getStats = false,
  setStats,
  onPlaying,
  onError,
}: WebRtcPlayerProps) {
  // metadata

  const wsURL = useMemo(() => {
    return `${baseUrl.replace(/^http/, "ws")}live/webrtc/api/ws?src=${camera}`;
  }, [camera]);

  // camera states

  const pcRef = useRef<RTCPeerConnection | undefined>();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [bufferTimeout, setBufferTimeout] = useState<NodeJS.Timeout>();
  const videoLoadTimeoutRef = useRef<NodeJS.Timeout>();

  const PeerConnection = useCallback(
    async (media: string) => {
      if (!videoRef.current) {
        return;
      }

      const pc = new RTCPeerConnection({
        bundlePolicy: "max-bundle",
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      const localTracks = [];

      if (/camera|microphone/.test(media)) {
        const tracks = await getMediaTracks("user", {
          video: media.indexOf("camera") >= 0,
          audio: media.indexOf("microphone") >= 0,
        });
        tracks.forEach((track) => {
          pc.addTransceiver(track, { direction: "sendonly" });
          if (track.kind === "video") localTracks.push(track);
        });
      }

      if (media.indexOf("display") >= 0) {
        const tracks = await getMediaTracks("display", {
          video: true,
          audio: media.indexOf("speaker") >= 0,
        });
        tracks.forEach((track) => {
          pc.addTransceiver(track, { direction: "sendonly" });
          if (track.kind === "video") localTracks.push(track);
        });
      }

      if (/video|audio/.test(media)) {
        const tracks = ["video", "audio"]
          .filter((kind) => media.indexOf(kind) >= 0)
          .map(
            (kind) =>
              pc.addTransceiver(kind, { direction: "recvonly" }).receiver.track,
          );
        localTracks.push(...tracks);
      }

      videoRef.current.srcObject = new MediaStream(localTracks);
      return pc;
    },
    [videoRef],
  );

  async function getMediaTracks(
    media: string,
    constraints: MediaStreamConstraints,
  ) {
    try {
      const stream =
        media === "user"
          ? await navigator.mediaDevices.getUserMedia(constraints)
          : await navigator.mediaDevices.getDisplayMedia(constraints);
      return stream.getTracks();
    } catch (e) {
      return [];
    }
  }

  const connect = useCallback(
    async (aPc: Promise<RTCPeerConnection | undefined>) => {
      console.log("connect", aPc);
      if (!aPc) {
        return;
      }

      pcRef.current = await aPc;
      let offer = await pcRef.current?.createOffer();
      console.log("offer", offer);
      offer = await pcRef.current?.createOffer();
      await pcRef.current?.setLocalDescription(offer);
      await new Promise<void>((resolve) => {
        pcRef.current?.addEventListener("icecandidate", (ev) => {
          console.log("icecandidate", ev.candidate);
          if (!ev.candidate) resolve();
        });
      });
      offer = await pcRef.current?.createOffer();
      await pcRef.current?.setLocalDescription(offer);
      const msg = {
        type: "webrtc/offer",
        sdp: pcRef.current?.localDescription?.sdp,
      };
      const body = JSON.stringify(msg);
      let res = await fetch("http://localhost:5000/api/sdp/offer", {
        method: "POST",
        body,
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-TOKEN": "1",
        },
      });

      if (!res.ok) {
        onError?.("startup");
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, 10000));
      console.log("fetching answer");
      res = await fetch("http://localhost:5000/api/sdp/answer", {
        method: "GET",
      });

      if (!res.ok) {
        onError?.("startup");
        return;
      }

      const data = await res.json();
      pcRef.current?.setRemoteDescription({
        type: "answer",
        sdp: data.sdp,
      });
    },
    [onError],
  );

  useEffect(() => {
    if (!videoRef.current) {
      return;
    }

    if (!playbackEnabled) {
      return;
    }
    console.log("help");

    const aPc = PeerConnection(
      microphoneEnabled ? "video+audio+microphone" : "video+audio",
    );
    connect(aPc);

    return () => {
      if (pcRef.current) {
        pcRef.current.close();
        pcRef.current = undefined;
      }
    };
  }, [
    camera,
    connect,
    PeerConnection,
    pcRef,
    videoRef,
    playbackEnabled,
    microphoneEnabled,
  ]);

  // ios compat

  const [iOSCompatControls, setiOSCompatControls] = useState(false);

  // control pip

  useEffect(() => {
    if (!videoRef.current || !pip) {
      return;
    }

    videoRef.current.requestPictureInPicture();
  }, [pip, videoRef]);

  // control volume

  useEffect(() => {
    if (!videoRef.current || volume == undefined) {
      return;
    }

    videoRef.current.volume = volume;
  }, [volume, videoRef]);

  useEffect(() => {
    videoLoadTimeoutRef.current = setTimeout(() => {
      onError?.("stalled");
    }, 5000);

    return () => {
      if (videoLoadTimeoutRef.current) {
        clearTimeout(videoLoadTimeoutRef.current);
      }
    };
    // we know that these deps are correct
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLoadedData = () => {
    if (videoLoadTimeoutRef.current) {
      clearTimeout(videoLoadTimeoutRef.current);
    }
    onPlaying?.();
  };

  // stats
  return (
    <video
      ref={videoRef}
      className={className}
      controls={iOSCompatControls}
      autoPlay
      playsInline
      muted={!audioEnabled}
      onLoadedData={handleLoadedData}
      onProgress={
        onError != undefined
          ? () => {
              if (videoRef.current?.paused) {
                return;
              }

              if (bufferTimeout) {
                clearTimeout(bufferTimeout);
                setBufferTimeout(undefined);
              }

              setBufferTimeout(
                setTimeout(() => {
                  if (
                    document.visibilityState === "visible" &&
                    pcRef.current != undefined
                  ) {
                    onError("stalled");
                  }
                }, 3000),
              );
            }
          : undefined
      }
      onClick={
        iOSCompatFullScreen
          ? () => setiOSCompatControls(!iOSCompatControls)
          : undefined
      }
      onError={(e) => {
        if (
          // @ts-expect-error code does exist
          e.target.error.code == MediaError.MEDIA_ERR_NETWORK
        ) {
          onError?.("startup");
        }
      }}
    />
  );
}
