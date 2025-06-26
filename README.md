# Python Tetris

Bu proje, temel Tetris oyununu Python ve Pygame kullanarak gerçekler. Oyunun hedefi doğadan esinlenen dört temel renkle (ateş, su, toprak, hava) hızlı ve eğlenceli bir Tetris deneyimi sunmaktır.

## Kurulum

Gereksinimleri yüklemek için:

```bash
pip install -r requirements.txt
```

Oyunu başlatmak için:

Windows:
```bash
set PYTHONPATH=src
python -m main
```
Linux/Mac:
```bash
export PYTHONPATH=src
python -m main
```

## Güncelleme Geçmişi

- Ilk sürüm: temel dosya yapısı oluşturuldu.
- Paket yapısı düzenlendi ve import sorunu giderildi.

## Derleme

`deploy.bat` betiği PyInstaller kullanarak Windows için tek bir `exe` dosyası
üretir. Derlemeden önce aşağıdaki gibi çalıştırabilirsiniz:

```bat
set PYTHONPATH=src
pyinstaller --onefile --name Tetris src/main.py
```

Android ve iOS için paketleme için Kivy/Buildozer gibi araçlar
yüklenebilir.
