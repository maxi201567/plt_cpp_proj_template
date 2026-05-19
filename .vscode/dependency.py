import json
import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))



def ensure_package_installed(package_name):
    try:
        __import__(package_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

for pkg in ["requests", "zipfile", "tarfile", "py7zr"]:
    ensure_package_installed(pkg)

def download_git_repo(repo_url, dest_dir, checkout_ref=None):
    try:
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        else:
            git_dir = os.path.join(dest_dir, ".git")
            if os.path.isdir(git_dir):
                try:
                    result = subprocess.run(
                        ['git', 'rev-parse', '--verify', checkout_ref],
                        cwd=dest_dir,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return result.returncode == 0
                finally:
                    return True
        subprocess.run(
            ['git', 'clone', repo_url, dest_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if checkout_ref:
            subprocess.run(
                ['git', 'checkout', checkout_ref],
                cwd=dest_dir,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return True
    except Exception as e:
        print(f"[git] 拉取失败: {e}")
        return False

def download_svn_repo(repo_url, dest_dir, branch_or_tag=None):
    try:
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        else:
            svn_dir = os.path.join(dest_dir, ".svn")
            if os.path.isdir(svn_dir):
                return True

        checkout_url = repo_url
        if branch_or_tag:
            if branch_or_tag.startswith('tags/'):
                checkout_url = f"{repo_url}/tags/{branch_or_tag[5:]}"
            elif branch_or_tag.startswith('branches/'):
                checkout_url = f"{repo_url}/branches/{branch_or_tag[9:]}"
            else:
                checkout_url = f"{repo_url}/branches/{branch_or_tag}"
        subprocess.run(['svn', 'checkout', checkout_url, dest_dir], check=True)
        return True
    except Exception as e:
        print(f"[svn] 拉取失败: {e}")
        return False

def download_http_archive(url, dest_dir):
    import requests
    import zipfile
    import tarfile
    import py7zr
    import lzma
    try:
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        else:
            if os.path.isdir(dest_dir) and any(os.scandir(dest_dir)):
                return True

        filename = url.split('/')[-1]
        archive_path = os.path.join(dest_dir, filename)

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(archive_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        if filename.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as archive:
                archive.extractall(dest_dir)
            os.remove(archive_path)
        elif filename.endswith('.tar.gz') or filename.endswith('.tgz'):
            with tarfile.open(archive_path, 'r:gz') as archive:
                archive.extractall(dest_dir)
            os.remove(archive_path)
        elif filename.endswith('.7z'):
            with py7zr.SevenZipFile(archive_path, mode='r') as archive:
                archive.extractall(dest_dir)
            os.remove(archive_path)
        else:
            raise ValueError(f"Unsupported archive format: {filename}")
        return True
    except Exception as e:
        print(f"[http] 拉取失败: {e}")
        return False

def load_dependencies():
    json_path = os.path.join(PROJECT_ROOT, "dependencies.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    dependencies = load_dependencies()

    for dep in dependencies:
        idx = dependencies.index(dep) + 1
        total = len(dependencies)
        print(f"[{idx}/{total}] : {dep['type']} {dep['url']} -> {dep['dest']}")
        result = False
        if dep["type"] == "git":
            result = download_git_repo(dep["url"], dep["dest"], dep.get("ref"))
        elif dep["type"] == "svn":
            result = download_svn_repo(dep["url"], dep["dest"], dep.get("ref"))
        elif dep["type"] == "http":
            result = download_http_archive(dep["url"], dep["dest"])
        else:
            print(f"未知类型: {dep['type']}")
            continue
        if not result:
            print(f"拉取失败: {dep['url']}")

    # 检测 cmake 是否存在
    try:
        result = subprocess.run(["cmake", "--version"], capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"[warning] cmake not found, skipping configuration ({e})")
        return

    for dep in dependencies:
        idx = dependencies.index(dep) + 1
        total = len(dependencies)
        print(f"[{idx}/{total}] : Config {dep['dest']}")
        args = dep.get("config_args")
        if args is not None:
            ret = subprocess.run(["cmake", "-S", dep['dest'], "-B", dep['dest'] + "/build", "-A", "x64"] + args.split(),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
            if ret.returncode != 0:
                print(ret.stderr)


if __name__ == "__main__":
    main()
