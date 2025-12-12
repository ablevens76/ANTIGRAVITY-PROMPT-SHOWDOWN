#!/bin/bash
# Generate sample videos WITH SPEECH AUDIO for testing TimeCapsule transcription
# Requires: ffmpeg, espeak-ng (for TTS)
#
# Install espeak-ng: sudo apt install espeak-ng

set -e

OUTPUT_DIR="${1:-./sample_videos}"

# ============================================================
# FAIL-FAST: Check required dependencies
# ============================================================
echo "🔍 Checking dependencies..."

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ERROR: ffmpeg not found"
    echo "   Install with: sudo apt install ffmpeg"
    exit 1
fi

if ! command -v espeak-ng &> /dev/null; then
    if ! command -v espeak &> /dev/null; then
        echo "❌ ERROR: espeak-ng not found"
        echo ""
        echo "   espeak-ng is required for generating sample videos with speech."
        echo "   This enables testing of the transcription pipeline."
        echo ""
        echo "   Install with:"
        echo "     sudo apt install espeak-ng    # Debian/Ubuntu/Pop!_OS"
        echo "     brew install espeak           # macOS"
        echo "     pacman -S espeak-ng           # Arch"
        echo ""
        echo "   Documentation: https://github.com/espeak-ng/espeak-ng"
        exit 1
    fi
    TTS_CMD="espeak"
else
    TTS_CMD="espeak-ng"
fi

echo "✅ ffmpeg found"
echo "✅ $TTS_CMD found"

mkdir -p "$OUTPUT_DIR"
echo ""
echo "🎬 Generating sample videos with TTS speech..."

# ============================================================
# Video 1: Welcome/intro
# ============================================================
echo "Creating video 1: welcome message..."
AUDIO1=$(mktemp --suffix=.wav)

$TTS_CMD -w "$AUDIO1" "Hello and welcome to Time Capsule. This is a test video for the transcription system." 2>/dev/null

ffmpeg -y \
    -f lavfi -i "color=c=0x1a1a2e:s=640x480:d=8" \
    -i "$AUDIO1" \
    -vf "drawtext=text='Welcome to TimeCapsule':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h/3,\
         drawtext=text='Testing Speech Recognition':fontsize=24:fontcolor=0xe94560:x=(w-text_w)/2:y=h/2" \
    -c:v libx264 -c:a aac -b:a 128k \
    -shortest \
    "$OUTPUT_DIR/welcome_test.mp4" \
    2>/dev/null

rm -f "$AUDIO1"
echo "✅ Created: $OUTPUT_DIR/welcome_test.mp4"

# ============================================================
# Video 2: Programming tutorial
# ============================================================
echo "Creating video 2: programming tutorial..."
AUDIO2=$(mktemp --suffix=.wav)

$TTS_CMD -w "$AUDIO2" "In this tutorial we will learn about Python programming. Variables are used to store data. Functions help organize code." 2>/dev/null

ffmpeg -y \
    -f lavfi -i "color=c=0x16213e:s=640x480:d=10" \
    -i "$AUDIO2" \
    -vf "drawtext=text='Python Tutorial':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h/4,\
         drawtext=text='def hello_world():':fontsize=28:fontcolor=0x4ade80:x=50:y=h/2:font=monospace,\
         drawtext=text='    print(Hello)':fontsize=28:fontcolor=0x4ade80:x=50:y=h/2+40:font=monospace" \
    -c:v libx264 -c:a aac -b:a 128k \
    -shortest \
    "$OUTPUT_DIR/python_tutorial.mp4" \
    2>/dev/null

rm -f "$AUDIO2"
echo "✅ Created: $OUTPUT_DIR/python_tutorial.mp4"

# ============================================================
# Video 3: Machine learning basics
# ============================================================
echo "Creating video 3: machine learning demo..."
AUDIO3=$(mktemp --suffix=.wav)

$TTS_CMD -w "$AUDIO3" "Machine learning models require training data. Neural networks learn patterns from examples. Deep learning is a subset of machine learning." 2>/dev/null

ffmpeg -y \
    -f lavfi -i "color=c=0x0f3460:s=640x480:d=10" \
    -i "$AUDIO3" \
    -vf "drawtext=text='Machine Learning Basics':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=h/3,\
         drawtext=text='Neural Networks and AI':fontsize=24:fontcolor=0xf093fb:x=(w-text_w)/2:y=h/2" \
    -c:v libx264 -c:a aac -b:a 128k \
    -shortest \
    "$OUTPUT_DIR/ml_basics.mp4" \
    2>/dev/null

rm -f "$AUDIO3"
echo "✅ Created: $OUTPUT_DIR/ml_basics.mp4"

# ============================================================
# Verify audio streams
# ============================================================
echo ""
echo "📊 Verifying audio streams..."
for f in "$OUTPUT_DIR"/*.mp4; do
    audio_streams=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$f" 2>/dev/null | wc -l)
    duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null | cut -d. -f1)
    if [ "$audio_streams" -gt 0 ]; then
        echo "  ✅ $(basename $f): has audio (${duration}s)"
    else
        echo "  ❌ $(basename $f): NO audio stream - transcription will fail!"
        exit 1
    fi
done

# List generated files
echo ""
echo "📂 Sample videos created in: $OUTPUT_DIR"
ls -lh "$OUTPUT_DIR"/*.mp4

echo ""
echo "🎤 Videos contain real TTS speech - Whisper will transcribe these!"
echo ""
echo "🚀 Next steps:"
echo "   timecapsule warmup           # Pre-load models"
echo "   timecapsule ingest $OUTPUT_DIR  # Process videos"
echo "   timecapsule serve            # Launch UI"
