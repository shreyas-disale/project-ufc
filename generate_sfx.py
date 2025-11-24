import wave, math, struct, os

os.makedirs('assets', exist_ok=True)

def make_wav(path,freq=440,dur=0.25,amp=0.3,sample_rate=44100):
    nframes = int(dur*sample_rate)
    with wave.open(path,'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(nframes):
            t = i/sample_rate
            val = int(amp*32767*math.sin(2*math.pi*freq*t))
            wf.writeframes(struct.pack('<h', val))

make_wav('assets/hit.wav', freq=880, dur=0.12, amp=0.4)
make_wav('assets/punch.wav', freq=600, dur=0.18, amp=0.35)
make_wav('assets/ko.wav', freq=220, dur=0.6, amp=0.5)
print('WAVs created')
