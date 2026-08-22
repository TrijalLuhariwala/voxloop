import asyncio
import edge_tts

async def main():
    try:
        print("Testing edge-tts with en-US-GuyNeural...")
        communicate = edge_tts.Communicate("Hello, this is VoxLoop testing the male AI voice.", voice="en-US-GuyNeural", rate="+20%")
        await communicate.save("scratch/test_guy.mp3")
        print("SUCCESS: scratch/test_guy.mp3 generated!")
    except Exception as e:
        print(f"FAILED edge-tts: {e}")

if __name__ == "__main__":
    asyncio.run(main())
