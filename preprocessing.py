import tensorflow as tf
import tensorflow_io as tfio


LABELS = ['yes','no']


class AudioReader():
    def __init__(self, resolution, sampling_rate):
        self.resolution = resolution
        self.sampling_rate = sampling_rate

    def get_audio(self, filename):
        audio_io_tensor = tfio.audio.AudioIOTensor(filename, self.resolution)        

        audio_tensor = audio_io_tensor.to_tensor()
        audio_tensor = tf.squeeze(audio_tensor)

        audio_float32 = tf.cast(audio_tensor, tf.float32)
        audio_normalized = audio_float32 / self.resolution.max

        zero_padding = tf.zeros(self.sampling_rate - tf.shape(audio_normalized), dtype=tf.float32)
        audio_padded = tf.concat([audio_normalized, zero_padding], axis=0)

        return audio_padded

    def get_label(self, filename):
        path_parts = tf.strings.split(filename, '/')
        path_end = path_parts[-1]
        file_parts = tf.strings.split(path_end, '_')
        label = file_parts[0]
        
        return label

    def get_audio_and_label(self, filename):
        audio = self.get_audio(filename)
        label = self.get_label(filename)

        return audio, label


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

    def get_mel_spec_and_label(self, audio, label):
        log_mel_spectrogram = self.get_mel_spec(audio)

        return log_mel_spectrogram, label


"""
trial mfcc
"""
"""
class MFCC():
    def __init__(
        self, 
        sampling_rate,
        frame_length_in_s,
        frame_step_in_s,
        num_mel_bins,
        lower_frequency,
        upper_frequency,
        num_coefficients
    ):
        self.mel_spectrogram_processor = MelSpectrogram(
            sampling_rate, frame_length_in_s, frame_step_in_s,
            num_mel_bins, lower_frequency, upper_frequency
        )
        num_mel_bins = self.mel_spectrogram_processor.linear_to_mel_weight_matrix.shape[0]
        self.num_coefficients = num_coefficients

        self.mfcc_filterbank = tf.signal.linear_to_mel_weight_matrix(
            num_mel_bins=num_mel_bins,
            num_spectrogram_bins=self.mel_spectrogram_processor.spectrogram_processor.frame_length // 2 + 1,
            sample_rate=sampling_rate,
            lower_edge_hertz=lower_frequency,
            upper_edge_hertz=upper_frequency
        )[:num_coefficients, :]

    def get_mfccs(self, audio):
        mel_spectrogram = self.mel_spectrogram_processor.get_mel_spec(audio)
        print("Shape - Mel Spectrogram:", mel_spectrogram.shape)
        print("Shape - MFCC Filterbank:", self.mfcc_filterbank.shape)

        # Transpose the MFCC filterbank
        mfcc_filterbank_transposed = tf.transpose(self.mfcc_filterbank)

        # Debugging prints
        print("MFCC Filterbank Transposed Shape:", mfcc_filterbank_transposed.shape)
        mel_spectrogram_shape = tf.shape(mel_spectrogram)

        # Check if dimensions match using assert_equal
        mel_spec_last_dim = mel_spectrogram_shape[-1]
        mfcc_filterbank_first_dim = mfcc_filterbank_transposed.shape[0]
        tf.debugging.assert_equal(
        mel_spec_last_dim,
        mfcc_filterbank_first_dim,
        message="Incompatible dimensions"
        )

        mfccs = tf.matmul(mel_spectrogram, mfcc_filterbank_transposed)
        mfccs = tf.math.log(mfccs + 1e-6)  # Logarithm for numerical stability

        return mfccs
    def get_mfccs_and_label(self, audio, label):
        mfccs = self.get_mfccs(audio)

        return mfccs, label
"""
"""
final mfcc
"""
class MFCC():
    def __init__(
        self, 
        sampling_rate,
        frame_length_in_s,
        frame_step_in_s,
        num_mel_bins,
        lower_frequency,
        upper_frequency,
        num_coefficients
    ):

        self.sampling_rate = sampling_rate
        self.frame_length_in_s = frame_length_in_s
        self.frame_step_in_s = frame_step_in_s
        self.num_mel_bins = num_mel_bins
        self.lower_frequency = lower_frequency
        self.upper_frequency = upper_frequency
        self.num_coefficients = num_coefficients
        self.log_mel_spectogram_processor = MelSpectrogram(sampling_rate,frame_length_in_s,frame_step_in_s,num_mel_bins,lower_frequency,upper_frequency)

    def get_mfccs(self, audio):
        log_mel_spectrogram = self.log_mel_spectogram_processor.get_mel_spec(audio)
        mfccs = tf.signal.mfccs_from_log_mel_spectrograms(log_mel_spectrogram)

        return mfccs
    def get_mfccs_and_label(self, audio, label):
        mfccs = self.get_mfccs(audio)

        return mfccs, label