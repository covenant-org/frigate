// Package main contains an example.
package main

import (
	"log"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"time"

	"github.com/bluenviron/gortsplib/v5"
	"github.com/bluenviron/gortsplib/v5/pkg/base"
	"github.com/bluenviron/gortsplib/v5/pkg/description"
	"github.com/bluenviron/gortsplib/v5/pkg/format"
	"github.com/gorilla/websocket"
	"github.com/pion/rtcp"
	"github.com/pion/rtp"
)

func main() {

	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	u := url.URL{Scheme: "ws", Host: "localhost:8000", Path: "/ws"}
	log.Printf("connecting to %s", u.String())

	c, _, err := websocket.DefaultDialer.Dial(u.String(), http.Header{
		"X-CSRF-TOKEN": []string{"1"},
	})
	if err != nil {
		log.Fatal("dial:", err)
	}
	defer c.Close()

	done := make(chan struct{})

	go func() {
		defer close(done)
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				log.Println("read:", err)
				return
			}
			log.Printf("recv: %s", message)
		}
	}()

	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-done:
			return
		case t := <-ticker.C:
			err := c.WriteMessage(websocket.TextMessage, []byte(t.String()))
			if err != nil {
				log.Println("write:", err)
				return
			}
		case <-interrupt:
			log.Println("interrupt")

			// Cleanly close the connection by sending a close message and then
			// waiting (with timeout) for the server to close the connection.
			err := c.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
			if err != nil {
				log.Println("write close:", err)
				return
			}
			select {
			case <-done:
			case <-time.After(time.Second):
			}
			return
		}
	}

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
