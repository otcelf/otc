import asyncio

async def main():
    print("Starting sleep...")
    await asyncio.sleep(5)
    print("Done sleep.")

if __name__ == "__main__":
    asyncio.run(main())
