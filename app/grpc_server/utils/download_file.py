import os
import time
import requests  # type: ignore
from tqdm import tqdm  # type: ignore


def download_file(
    url: str,
    save_path: str,
    retries: int = 10,
) -> None:

    print('Download:', save_path)

    # 保存先ディレクトリがなければ作成
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    for attempt in range(retries):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            with open(save_path, 'wb') as file, tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=save_path,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    pbar.update(len(chunk))
            return
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                print(f"[Retry {attempt + 1}] {e}")
                time.sleep(5)
            else:
                raise RuntimeError(f"Failed to download {url} after {retries} attempts") from e
