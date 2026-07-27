#!/usr/bin/env python3
"""
Split one long recording into the twelve sound files the mod wants.

    python3 prepare.py margot-sounds.wav

Give it a single recording containing the twelve takes in the documented order,
separated by silence. It finds the gaps, cuts the clips out, names them, drops
them next to this script, and rewrites sounds.json to use them instead of the
vanilla placeholders.

Splitting needs nothing but Python. Minecraft only plays **OGG Vorbis**, so the
final encode needs ffmpeg -- if ffmpeg is on your PATH this script does it for
you, and if not it writes WAVs and prints the one command to finish the job.
"""
import argparse, json, math, os, struct, subprocess, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDS_JSON = os.path.join(HERE, '..', 'src', 'main', 'resources',
                           'assets', 'roussette', 'sounds.json')

# Recording order. (event, take-count) -- 12 clips total.
ORDER = [
    ('cry',     3),
    ('wail',    2),
    ('purr',    1),
    ('purreow', 1),
    ('chomp',   2),
    ('gnaw',    1),
    ('eep',     1),
    ('huff',    1),
]
EXPECTED = sum(n for _, n in ORDER)


def names():
    out = []
    for event, n in ORDER:
        for i in range(1, n + 1):
            out.append(f'{event}{i}' if n > 1 else event)
    return out


def load_wav(path):
    """-> (samplerate, [mono float samples])"""
    with wave.open(path, 'rb') as w:
        ch, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(frames)
    if width == 2:
        fmt, peak = '<%dh' % (len(raw) // 2), 32768.0
    elif width == 1:
        data = [(b - 128) / 128.0 for b in raw]
        return rate, [sum(data[i:i+ch]) / ch for i in range(0, len(data), ch)]
    elif width == 4:
        fmt, peak = '<%di' % (len(raw) // 4), 2147483648.0
    else:
        sys.exit(f'unsupported sample width: {width*8}-bit. Export 16-bit WAV.')
    vals = struct.unpack(fmt, raw)
    if ch == 1:
        return rate, [v / peak for v in vals]
    return rate, [sum(vals[i:i+ch]) / ch / peak for i in range(0, len(vals), ch)]


def decode_with_ffmpeg(path):
    tmp = os.path.join(HERE, '.decoded.wav')
    print(f'  not a WAV; decoding with ffmpeg -> {os.path.basename(tmp)}')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path,
                    '-ac', '1', '-ar', '44100', tmp], check=True)
    return tmp


def envelope(samples, rate, window_ms=20):
    """RMS per short window -- steadier than raw amplitude for finding gaps."""
    win = max(1, int(rate * window_ms / 1000))
    out = []
    for i in range(0, len(samples), win):
        chunk = samples[i:i+win]
        out.append(math.sqrt(sum(s*s for s in chunk) / len(chunk)) if chunk else 0.0)
    return out, win


def find_clips(samples, rate, min_gap_s, floor_mult, pad_ms):
    env, win = envelope(samples, rate)
    if not env:
        sys.exit('empty recording')
    quiet = sorted(env)[:max(1, len(env)//5)]
    noise = sum(quiet) / len(quiet)
    peak = max(env)
    thresh = max(noise * floor_mult, peak * 0.035)

    loud = [e > thresh for e in env]
    min_gap_win = max(1, int(min_gap_s * 1000 / 20))

    clips, start, gap = [], None, 0
    for i, is_loud in enumerate(loud):
        if is_loud:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= min_gap_win:
                clips.append((start, i - gap))
                start, gap = None, 0
    if start is not None:
        clips.append((start, len(loud) - 1))

    pad = int(pad_ms / 20)
    out = []
    for a, b in clips:
        a = max(0, a - pad); b = min(len(env) - 1, b + pad)
        s0, s1 = a * win, min(len(samples), (b + 1) * win)
        if (s1 - s0) / rate >= 0.06:          # drop anything under 60 ms
            out.append((s0, s1))
    return out, thresh, noise, peak


def write_wav(path, rate, samples):
    peak = max((abs(s) for s in samples), default=0.0) or 1.0
    gain = min(1.0, 0.89 / peak)              # normalise, leave headroom
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b''.join(
            struct.pack('<h', max(-32768, min(32767, int(s * gain * 32767))))
            for s in samples))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('recording')
    ap.add_argument('--min-gap', type=float, default=0.45,
                    help='seconds of silence that separates two takes (default 0.45)')
    ap.add_argument('--floor', type=float, default=4.0,
                    help='how far above the noise floor counts as sound (default 4.0)')
    ap.add_argument('--pad', type=float, default=60,
                    help='ms of padding kept around each clip (default 60)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    path = args.recording
    if not path.lower().endswith('.wav'):
        if not shutil_which('ffmpeg'):
            sys.exit('Not a WAV, and ffmpeg is not installed.\n'
                     'Either export a 16-bit WAV, or install ffmpeg.')
        path = decode_with_ffmpeg(path)

    rate, samples = load_wav(path)
    print(f'  {len(samples)/rate:.1f}s at {rate} Hz')

    clips, thresh, noise, peak = find_clips(samples, rate, args.min_gap, args.floor, args.pad)
    print(f'  noise floor {noise:.4f}, peak {peak:.3f}, threshold {thresh:.4f}')
    print(f'  found {len(clips)} clips (expected {EXPECTED})\n')

    want = names()
    for i, (a, b) in enumerate(clips):
        label = want[i] if i < len(want) else '(extra)'
        print(f'    {i+1:>2}. {label:<10} {a/rate:7.2f}s  {(b-a)/rate:5.2f}s long')

    if len(clips) != EXPECTED:
        print(f'\n  Clip count is {len(clips)}, not {EXPECTED}.')
        print('  Nothing written. Try adjusting the split:')
        print('    --min-gap 0.30   if two takes ran together (too few clips)')
        print('    --min-gap 0.80   if one take got cut in half (too many clips)')
        print('    --floor 6.0      if room noise is being picked up as takes')
        sys.exit(1)

    if args.dry_run:
        print('\n  --dry-run: nothing written.')
        return

    have_ffmpeg = shutil_which('ffmpeg')
    written = []
    for name, (a, b) in zip(want, clips):
        wav = os.path.join(HERE, name + '.wav')
        write_wav(wav, rate, samples[a:b])
        if have_ffmpeg:
            ogg = os.path.join(HERE, name + '.ogg')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav,
                            '-ac', '1', '-c:a', 'libvorbis', '-q:a', '5', ogg], check=True)
            os.remove(wav)
            written.append(name + '.ogg')
        else:
            written.append(name + '.wav')

    print('\n  wrote: ' + ', '.join(written))
    rewrite_sounds_json(have_ffmpeg)

    if not have_ffmpeg:
        print('\n  ffmpeg not found, so these are WAVs. Minecraft needs OGG.')
        print('  Finish with:')
        print('    for f in *.wav; do ffmpeg -i "$f" -ac 1 -c:a libvorbis -q:a 5 "${f%.wav}.ogg"; done')
        print('  (or open each in Audacity and File > Export > Export as OGG)')


def rewrite_sounds_json(have_ffmpeg):
    """Point every vocal event at the new takes; leave the wet ones on vanilla."""
    with open(SOUNDS_JSON) as f:
        data = json.load(f)
    for event, n in ORDER:
        takes = [f'roussette:{event}{i}' if n > 1 else f'roussette:{event}'
                 for i in range(1, n + 1)]
        data[event] = {
            'category': 'hostile',
            'subtitle': data.get(event, {}).get('subtitle', f'subtitles.roussette.{event}'),
            'sounds': takes,
        }
    with open(SOUNDS_JSON, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
    print(f'  updated {os.path.relpath(SOUNDS_JSON, HERE)}')
    print('  squelch and reform left on the vanilla slime/splash sounds.')


def shutil_which(name):
    from shutil import which
    return which(name)


if __name__ == '__main__':
    main()
