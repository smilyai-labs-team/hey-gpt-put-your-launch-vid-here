# Playable MP4 assembly
The media parts in `film.parts/` are consecutive byte slices of the **complete 327.658-second, 1920×1080, 30 fps, H.264/AAC launch film**.

This repository includes a GitHub Actions workflow that concatenates the binary parts in order, verifies the SHA-256 checksum, and commits the resulting file at the root:

**`Orion_T3_Flash_Official_Launch_1080p.mp4`**

Verification SHA-256: `c9b0f7e1e59da5c3502902547bf3aa727a25e66bb074ae154dd63fce7f3ad459`.

The original highest-quality 35 MB master and the editable production ZIP are separately provided in the ChatGPT conversation. This GitHub edition is a smaller browser-friendly encoding preserving Full HD and the full song.

If the assembly workflow doesn't start automatically, use the repository's **Actions** tab → **Assemble Orion T3 Flash launch film** → **Run workflow**. Nothing should be described as published until the finished MP4 exists.
