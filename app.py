import asyncio
import os
import sys

# Убедиться, что корневой каталог проекта находится в sys.path
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

from bot.main import main

if __name__ == "__main__":
    asyncio.run(main())
