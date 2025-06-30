import os
from time import time
import tensorflow as tf
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import argparse

resolution='int16'
sample_rate=16000
frame_length_in_s=0.032
frame_step=0.05
num_mel_bins=10
lower_frequency=0
upper_frequency=8000
channels=1
duration=0.5 
dbfsthres=-45
duration_thres=0.1
blocksize=int(duration*sample_rate)
audio_buffer=np.zeros(shape=(sample_rate, 1))

#Mel spectogram
class Spectrogram():
    def __init__(self, sampling_rate, frame_length_in_s, frame_step_in_s):
        self.frame_length = int(frame_length_in_s * sampling_rate)
        self.frame_step = int(frame_step_in_s * sampling_rate)

    def get_spectrogram(self, audio):
        stft = tf.signal.stft(
            audio, 
            frame_length=self.frame_length,
            frame_step=self.frame_step,
            fft_length=self.frame_length
        )
        spectrogram = tf.abs(stft)
        return spectrogram

    def get_spectrogram_and_label(self, audio, label):
        audio = get_spectrogram(audio)
        return spectrogram, label

class MelSpectrogram():
    def __init__(
        self, 
        sampling_rate,
        frame_length_in_s,
        frame_step_in_s,
        num_mel_bins,
        lower_frequency,
        upper_frequency
    ):
        self.spectrogram_processor = Spectrogram(sampling_rate, frame_length_in_s, frame_step_in_s)
        num_spectrogram_bins = self.spectrogram_processor.frame_length // 2 + 1

        self.linear_to_mel_weight_matrix = tf.signal.linear_to_mel_weight_matrix(
            num_mel_bins=num_mel_bins,
            num_spectrogram_bins=num_spectrogram_bins,
            sample_rate=sampling_rate,
            lower_edge_hertz=lower_frequency,
            upper_edge_hertz=upper_frequency
        )

    def get_mel_spec(self, audio):
        spectrogram = self.spectrogram_processor.get_spectrogram(audio)
        mel_spectrogram = tf.matmul(spectrogram, self.linear_to_mel_weight_matrix)
        log_mel_spectrogram = tf.math.log(mel_spectrogram + 1.e-6)

        return log_mel_spectrogram

#VAD class
class VAD():
    def __init__(
        self,
        sampling_rate,
        frame_length_in_s,
        num_mel_bins,
        lower_frequency,
        upper_frequency,
        dbFSthres, 
        duration_thres
    ):
        self.frame_length_in_s = frame_length_in_s
        self.mel_spec_processor = MelSpectrogram(
            sampling_rate, frame_length_in_s, frame_length_in_s, num_mel_bins, lower_frequency, upper_frequency
        )
        self.dbFSthres = dbFSthres
        self.duration_thres = duration_thres

    def is_silence(self, audio):
        audio_reader = AudioReader(tf.int16, sample_rate)
        audio = audio_reader.get_audio(indata=audio)
        mel_spec_processor = MelSpectrogram(sample_rate, frame_length_in_s, frame_step, num_mel_bins, lower_frequency, upper_frequency)
        log_mel_spec = self.mel_spec_processor.get_mel_spec(audio)
        dbFS = 20 * log_mel_spec
        energy = tf.math.reduce_mean(dbFS, axis=1)

        non_silence = energy > self.dbFSthres
        non_silence_frames = tf.math.reduce_sum(tf.cast(non_silence, tf.float32))
        non_silence_duration = (non_silence_frames + 1) * self.frame_length_in_s

        if non_silence_duration > self.duration_thres:
            return 0
        else:
            return 1

#Audio normalized Class
class AudioReader():
    def __init__(self, resolution, sampling_rate):
        self.resolution = resolution
        self.sampling_rate = sampling_rate

    def get_audio(self,indata):
        # TensorFlow tensor
        audio_tensor = tf.convert_to_tensor(indata, dtype=tf.float32)
        # Squeezing the tensor 
        squeezed_tensor = tf.squeeze(audio_tensor)
        # Normalizing the tensor 
        audio_normalized = squeezed_tensor/tf.int16.max

        return audio_normalized
    
audio_reader = AudioReader(tf.int16, sample_rate)
    

def callback(indata, frames, callback_time, status):
    global audio_buffer, store_audio
    audio_buffer=np.roll(audio_buffer,blocksize)
    print(audio_buffer.shape,indata.shape)
    audio_buffer[blocksize:,:] = indata
    
    store_audio = bool(vad.is_silence(audio_buffer))
    
    if not store_audio: 
        timestamp = time()
        write(f'{timestamp}.wav', 16000, indata)
        filesize_in_bytes = os.path.getsize(f'{timestamp}.wav')
        filesize_in_kb = filesize_in_bytes / 1024
        print(f'Size: {filesize_in_kb:.2f}KB')

parser = argparse.ArgumentParser()
parser.add_argument('--device', type=int, default=1,help='ID of the microphone device for recording')
args = parser.parse_args()

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--device', type=int, default=1,help='ID of the microphone device for recording')
        args = parser.parse_args()
        store_audio = True
        vad = VAD(sampling_rate = sample_rate, frame_length_in_s=frame_length_in_s, num_mel_bins=num_mel_bins, lower_frequency=lower_frequency, upper_frequency=upper_frequency,dbFSthres=dbfsthres,duration_thres=duration_thres)
        with sd.InputStream(device=args.device, channels=channels, dtype=resolution, samplerate=sample_rate, blocksize=blocksize, callback=callback):
            while True:
                key = input()
                if key in ('q', 'Q'):
                    print('Stop recording.')
                    break
        # process_audio_frame(indata)
    except KeyboardInterrupt:
        print('\nRecording stopped.')