package main

import (
	"encoding/json"
	"fmt"
	"log"

	"github.com/bluenviron/gortsplib/v5"
	"github.com/bluenviron/gortsplib/v5/pkg/base"
	"github.com/bluenviron/gortsplib/v5/pkg/description"
	"github.com/bluenviron/gortsplib/v5/pkg/format"
	"github.com/pion/rtcp"
	"github.com/pion/rtp"
	"github.com/pion/webrtc/v4"
	"resty.dev/v3"
)

type SDPRequest struct {
	SDP  string `json:"sdp"`
	Type string `json:"type"`
}

func main() {
	u, err := base.ParseURL("rtsp://localhost:8558/bunny")
	if err != nil {
		panic(err)
	}

	c := gortsplib.Client{
		Scheme: u.Scheme,
		Host:   u.Host,
	}

	err = c.Start()
	if err != nil {
		panic(err)
	}
	defer c.Close()

	desc, _, err := c.Describe(u)
	if err != nil {
		panic(err)
	}

	log.Printf("Available medias: %v\n", desc.Medias)
	if desc.Medias == nil || len(desc.Medias) == 0 {
		panic("no medias found")
	}

	// setup all medias
	err = c.SetupAll(desc.BaseURL, desc.Medias)
	if err != nil {
		panic(err)
	}

	peerConnection, err := webrtc.NewPeerConnection(webrtc.Configuration{
		ICEServers: []webrtc.ICEServer{
			{
				URLs: []string{"stun:stun.l.google.com:19302"},
			},
		},
	})
	if err != nil {
		panic(err)
	}
	var rtpSender *webrtc.RTPSender
	var track *webrtc.TrackLocalStaticRTP

	// for each media, create a corresponding WebRTC track
	for _, medi := range desc.Medias {
		var codec webrtc.RTPCodecCapability
		var mediType string

		switch medi.Type {
		case description.MediaTypeVideo:
			codec = webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypeVP8}
			mediType = "video"
		case description.MediaTypeAudio:
			codec = webrtc.RTPCodecCapability{MimeType: webrtc.MimeTypePCMU}
			mediType = "audio"
			continue
		default:
			log.Printf("unsupported media type: %v\n", medi.Type)
			continue
		}

		track, err = webrtc.NewTrackLocalStaticRTP(
			codec,
			mediType,
			"pion",
		)
		if err != nil {
			panic(err)
		}

		rtpSender, err = peerConnection.AddTrack(track)
		if err != nil {
			panic(err)
		}

		go func() {
			rtcpBuf := make([]byte, 1500)
			for {
				if _, _, rtcpErr := rtpSender.Read(rtcpBuf); rtcpErr != nil {
					return
				}
			}
		}()
	}

	// Set the handler for ICE connection state
	// This will notify you when the peer has connected/disconnected
	peerConnection.OnICEConnectionStateChange(func(connectionState webrtc.ICEConnectionState) {
		fmt.Printf("Connection State has changed %s \n", connectionState.String())

		if connectionState == webrtc.ICEConnectionStateFailed {
			if closeErr := peerConnection.Close(); closeErr != nil {
				panic(closeErr)
			}
		}
	})

	// Wait for the offer to be pasted
	httpClient := resty.New()
	defer httpClient.Close()
	res, err := httpClient.R().Get("http://localhost:5000/api/sdp/offer")
	if err != nil {
		panic(err)
	}
	fmt.Printf("SDP offer response received:\n%v\n", res.String())
	var resq SDPRequest
	err = json.Unmarshal(res.Bytes(), &resq)
	if err != nil {
		panic(err)
	}

	offer := webrtc.SessionDescription{}
	fmt.Printf("SDP offer received:\n%v\n", resq.SDP)
	offer.SDP = resq.SDP
	offer.Type = webrtc.SDPTypeOffer

	// Set the remote SessionDescription
	if err = peerConnection.SetRemoteDescription(offer); err != nil {
		panic(err)
	}

	// Create answer
	answer, err := peerConnection.CreateAnswer(nil)
	if err != nil {
		panic(err)
	}

	// Create channel that is blocked until ICE Gathering is complete
	gatherComplete := webrtc.GatheringCompletePromise(peerConnection)

	// Sets the LocalDescription, and starts our UDP listeners
	if err = peerConnection.SetLocalDescription(answer); err != nil {
		panic(err)
	}

	// Block until ICE Gathering is complete, disabling trickle ICE
	// we do this because we only can exchange one signaling message
	// in a production application you should exchange ICE Candidates via OnICECandidate
	<-gatherComplete

	ldesc := peerConnection.LocalDescription()
	_, err = httpClient.R().SetBody(SDPRequest{
		SDP:  ldesc.SDP,
		Type: ldesc.Type.String(),
	}).SetHeader("X-CSRF-TOKEN", "1").Post("http://localhost:5000/api/sdp/answer")
	if err != nil {
		panic(err)
	}

	// called when a RTP packet arrives
	c.OnPacketRTPAny(func(medi *description.Media, _ format.Format, packet *rtp.Packet) {
		track.WriteRTP(packet)
		log.Printf("RTP packet from media %v\n", medi.Type)
	})

	// called when a RTCP packet arrives
	c.OnPacketRTCPAny(func(medi *description.Media, pkt rtcp.Packet) {
		log.Printf("RTCP packet from media %v, type %T\n", medi, pkt)
	})

	// start playing
	_, err = c.Play(nil)
	if err != nil {
		panic(err)
	}

	// wait until a fatal error
	panic(c.Wait())
}
