import shutil
import wave
import os

from app import App


from pydub import AudioSegment

# 或Linux/macOS
AudioSegment.ffmpeg = "/usr/local/bin/ffmpeg"

sil_supports = [8000, 12000, 16000, 24000, 32000, 44100, 48000]  # slk转wav时，支持的采样率

def find_closest_sil_supports(sample_rate):
    """
    找到最接近的支持的采样率
    """
    if sample_rate in sil_supports:
        return sample_rate
    closest = 0
    mindiff = 9999999
    for rate in sil_supports:
        diff = abs(rate - sample_rate)
        if diff < mindiff:
            closest = rate
            mindiff = diff
    return closest


def get_pcm_from_wav(wav_path):
    """
    从 wav 文件中读取 pcm

    :param wav_path: wav 文件路径
    :returns: pcm 数据
    """
    wav = wave.open(wav_path, "rb")
    return wav.readframes(wav.getnframes())


def any_to_mp3(input_path: str, output_path: str = None) -> str:
    """将任意音频格式转换为MP3格式
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（可选）
    Returns:
        转换后的文件路径
    """
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".mp3"

    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3", bitrate="192k")
        return output_path
    except Exception as e:
        raise RuntimeError(f"音频转换失败: {str(e)}")


def any_to_wav(any_path, wav_path):
    """
    把任意格式转成wav文件
    """
    if any_path.endswith(".wav"):
        shutil.copy2(any_path, wav_path)
        return
    if any_path.endswith(".sil") or any_path.endswith(".silk") or any_path.endswith(".slk"):
        return sil_to_wav(any_path, wav_path)
    audio = AudioSegment.from_file(any_path)
    audio.set_frame_rate(8000)    # 百度语音转写支持8000采样率, pcm_s16le, 单通道语音识别
    audio.set_channels(1)
    audio.export(wav_path, format="wav", codec='pcm_s16le')


def encode_silk(pcm_data: bytes, sample_rate: int) -> bytes:
    """使用silk-v3-encoder进行编码"""
    from subprocess import Popen, PIPE
    with Popen(['silk_encoder', str(sample_rate), '-', '-'], stdin=PIPE, stdout=PIPE) as proc:
        return proc.communicate(pcm_data)[0]

def decode_silk(silk_data: bytes, sample_rate: int) -> bytes:
    """使用silk-v3-decoder进行解码"""
    from subprocess import Popen, PIPE
    with Popen(['silk_decoder', '-', '-', '-Fs_API', str(sample_rate)], stdin=PIPE, stdout=PIPE) as proc:
        return proc.communicate(silk_data)[0]

def any_to_sil(any_path, sil_path):
    """
    把任意格式转成sil文件
    """
    if any_path.endswith(".sil") or any_path.endswith(".silk") or any_path.endswith(".slk"):
        shutil.copy2(any_path, sil_path)
        return 10000
    audio = AudioSegment.from_file(any_path)
    rate = find_closest_sil_supports(audio.frame_rate)
    # Convert to PCM_s16
    pcm_s16 = audio.set_sample_width(2)
    pcm_s16 = pcm_s16.set_frame_rate(rate)
    wav_data = pcm_s16.raw_data
    try:
        silk_data = encode_silk(wav_data, rate)
    except Exception as e:
        print(f"编码失败！请安装silk-v3-encoder: https://github.com/kn007/silk-v3-decoder")
        raise
    with open(sil_path, "wb") as f:
        f.write(silk_data)
    return audio.duration_seconds * 1000


def any_to_amr(any_path, amr_path):
    """
    把任意格式转成amr文件
    """
    if any_path.endswith(".amr"):
        shutil.copy2(any_path, amr_path)
        return
    if any_path.endswith(".sil") or any_path.endswith(".silk") or any_path.endswith(".slk"):
        raise NotImplementedError("Not support file type: {}".format(any_path))
    audio = AudioSegment.from_file(any_path)
    audio = audio.set_frame_rate(8000)  # only support 8000
    audio.export(amr_path, format="amr")
    return audio.duration_seconds * 1000


def sil_to_wav(silk_path, wav_path, rate: int = 24000):
    """
    silk 文件转 wav
    """
    with open(silk_path, 'rb') as f:
        silk_data = f.read()
    wav_data = decode_silk(silk_data, rate)
    with open(wav_path, "wb") as f:
        f.write(wav_data)


def split_audio(file_path, max_segment_length_ms=60000):
    """
    分割音频文件
    """
    audio = AudioSegment.from_file(file_path)
    audio_length_ms = len(audio)
    if audio_length_ms <= max_segment_length_ms:
        return audio_length_ms, [file_path]
    segments = []
    for start_ms in range(0, audio_length_ms, max_segment_length_ms):
        end_ms = min(audio_length_ms, start_ms + max_segment_length_ms)
        segment = audio[start_ms:end_ms]
        segments.append(segment)
    file_prefix = file_path[: file_path.rindex(".")]
    format = file_path[file_path.rindex(".") + 1 :]
    files = []
    for i, segment in enumerate(segments):
        path = f"{file_prefix}_{i+1}" + f".{format}"
        segment.export(path, format=format)
        files.append(path)
    return audio_length_ms, files

# 在文件底部添加__all__导出声明
__all__ = ['any_to_mp3', 'any_to_wav', 'split_audio']
