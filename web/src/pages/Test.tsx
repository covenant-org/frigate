import WebRtcPlayer from "@/components/player/WebRTCPlayer";

function Test() {
  return (
    <div className="flex size-full flex-col p-2">
      <WebRtcPlayer camera="test_camera" />
    </div>
  );
}

export default Test;
