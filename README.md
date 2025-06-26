# Python Tetris

Bu proje, temel Tetris oyununu Python ve Pygame kullanarak gerçekler. Oyunun hedefi doğadan esinlenen dört temel renkle (ateş, su, toprak, hava) hızlı ve eğlenceli bir Tetris deneyimi sunmaktır.

## Kurulum

Gereksinimleri yüklemek için:

```bash
pip install -r requirements.txt
```

Oyunu başlatmak için:

```bash
python src/main.py
```

## Güncelleme Geçmişi

- Ilk sürüm: temel dosya yapısı oluşturuldu.
- Paket yapısı düzenlendi ve import sorunu giderildi.
- `src/main.py` mutlak import kullanacak şekilde güncellendi.

## Derleme

`deploy.bat` betiği PyInstaller kullanarak Windows için tek bir `exe` dosyası
üretir. Android ve iOS için paketleme için Kivy/Buildozer gibi araçlar
yüklenebilir.
