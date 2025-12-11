// Package main contains an example.
package main

import (
	"github.com/bluenviron/gortsplib/v5"
	"github.com/bluenviron/gortsplib/v5/pkg/base"
	"github.com/bluenviron/gortsplib/v5/pkg/description"
	"github.com/bluenviron/gortsplib/v5/pkg/format"
	"github.com/pion/rtcp"
	"github.com/pion/rtp"
)

func main() {
	in, err := base.ParseURL("rtsp://localhost:8554/bunny")
	if err != nil {
		panic(err)
	}

	inc := gortsplib.Client{
		Scheme: in.Scheme,
		Host:   in.Host,
	}

	// connect to the server
	err = inc.Start()
	if err != nil {
		panic(err)
	}
	defer inc.Close()

	// find available medias
	desc, _, err := inc.Describe(in)
	if err != nil {
		panic(err)
	}

	inc.SetupAll(in, desc.Medias)

	outc := gortsplib.Client{}
	outc.StartRecording("rtsp://localhost:8554/output", desc)

	defer outc.Close()

	inc.OnPacketRTPAny(func(media *description.Media, format format.Format, pkt *rtp.Packet) {
		outc.WritePacketRTP(media, pkt)
	})

	inc.OnPacketRTCPAny(func(media *description.Media, pkt rtcp.Packet) {
		outc.WritePacketRTCP(media, pkt)
	})

	if _, err = inc.Play(nil); err != nil {
		panic(err)
	}

	panic(inc.Wait())
}
