from pathlib import Path
import re

p = Path('ATLAS-v025/app/src/main/java/com/atlas/survey/MainActivity.java')
s = p.read_text(encoding='utf-8')

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'Missing source block: {label}')
    s = s.replace(old, new, 1)

old = '''            double maxLon = Double.NEGATIVE_INFINITY, maxLat = Double.NEGATIVE_INFINITY;
            for (int i = 0; i < pts.length(); i++) {
                JSONArray p = pts.optJSONArray(i);
                if (p == null || p.length() < 2) continue;
                double lon = p.optDouble(0, Double.NaN), lat = p.optDouble(1, Double.NaN);
                if (!Double.isFinite(lon) || !Double.isFinite(lat)) continue;
                minLon = Math.min(minLon, lon); maxLon = Math.max(maxLon, lon);
                minLat = Math.min(minLat, lat); maxLat = Math.max(maxLat, lat);
            }
            if (!Double.isFinite(minLon) || !Double.isFinite(minLat)) throw new IllegalArgumentException("Polygon koordinatları geçersiz.");
            int lon0 = (int) Math.floor(minLon), lon1 = (int) Math.floor(maxLon);
            int lat0 = (int) Math.floor(minLat), lat1 = (int) Math.floor(maxLat);'''
new = '''            double maxLon = Double.NEGATIVE_INFINITY, maxLat = Double.NEGATIVE_INFINITY;
            int validPoints = 0;
            for (int i = 0; i < pts.length(); i++) {
                JSONArray p = pts.optJSONArray(i);
                if (p == null || p.length() < 2) continue;
                double lon = p.optDouble(0, Double.NaN), lat = p.optDouble(1, Double.NaN);
                if (!Double.isFinite(lon) || !Double.isFinite(lat)) continue;
                if (lon < -180.0 || lon > 180.0 || lat < -90.0 || lat > 90.0) {
                    throw new IllegalArgumentException("Polygon koordinatı WGS84 aralığı dışında: " + lon + ", " + lat);
                }
                validPoints++;
                minLon = Math.min(minLon, lon); maxLon = Math.max(maxLon, lon);
                minLat = Math.min(minLat, lat); maxLat = Math.max(maxLat, lat);
            }
            if (validPoints < 3 || !Double.isFinite(minLon) || !Double.isFinite(minLat)) {
                throw new IllegalArgumentException("Polygon koordinatları geçersiz.");
            }
            if (maxLon - minLon > 5.0 || maxLat - minLat > 5.0) {
                throw new IllegalArgumentException("Çalışma alanı GLO-30 mobil indirme için çok geniş. Daha küçük bir alan seçin veya yerel DEM kullanın.");
            }
            double maxLonInside = (maxLon > minLon) ? Math.nextAfter(maxLon, Double.NEGATIVE_INFINITY) : maxLon;
            double maxLatInside = (maxLat > minLat) ? Math.nextAfter(maxLat, Double.NEGATIVE_INFINITY) : maxLat;
            int lon0 = (int) Math.floor(minLon), lon1 = (int) Math.floor(maxLonInside);
            int lat0 = (int) Math.floor(minLat), lat1 = (int) Math.floor(maxLatInside);'''
replace_once(old,new,'bounds')

old = '''                    if (!out.isFile() || out.length() < 1024L * 1024L) {
                        if (out.exists()) out.delete();
                        sendCopernicusProgress(index - 1, tileCount, "Copernicus indiriliyor · " + tile);
                        downloadCopernicusTile(tile, out, index - 1, tileCount);
                    } else {
                        sendCopernicusProgress(index - 1, tileCount, "DEM önbellekten · " + tile);
                    }
                    files.add(out);
                    sendCopernicusProgress(index, tileCount, "Copernicus hazır · " + index + "/" + tileCount);
                }
            }
            JSONObject info = demSampler.loadFiles(files, "Copernicus GLO-30 · " + tileCount + " karo");'''
new = '''                    if (!isUsableCopernicusTile(out)) {
                        if (out.exists() && !out.delete()) throw new IllegalStateException("Bozuk DEM önbelleği silinemedi: " + tile);
                        sendCopernicusProgress(index - 1, tileCount, "GLO-30 indiriliyor · " + tile);
                        downloadCopernicusTile(tile, out, index - 1, tileCount);
                    } else {
                        sendCopernicusProgress(index - 1, tileCount, "GLO-30 önbellekten · " + tile);
                    }
                    files.add(out);
                    sendCopernicusProgress(index, tileCount, "GLO-30 hazır · " + index + "/" + tileCount);
                }
            }
            JSONObject info;
            try {
                info = demSampler.loadFiles(files, "Copernicus GLO-30 · " + tileCount + " karo");
            } catch (Exception firstRead) {
                sendCopernicusProgress(0, tileCount, "GLO-30 cache doğrulanamadı · yeniden indiriliyor");
                for (File f : files) if (f.exists()) f.delete();
                files.clear();
                index = 0;
                for (int lat = lat0; lat <= lat1; lat++) {
                    for (int lon = lon0; lon <= lon1; lon++) {
                        index++;
                        String tile = copernicusTileName(lat, lon);
                        File out = new File(cache, tile + ".tif");
                        downloadCopernicusTile(tile, out, index - 1, tileCount);
                        files.add(out);
                    }
                }
                info = demSampler.loadFiles(files, "Copernicus GLO-30 · " + tileCount + " karo");
            }'''
replace_once(old,new,'cache')

old = '''    private void downloadCopernicusTile(String tile, File out, int completed, int total) throws Exception {
        String url = "https://copernicus-dem-30m.s3.amazonaws.com/" + tile + "/" + tile + ".tif";'''
new = '''    private boolean isUsableCopernicusTile(File file) {
        if (file == null || !file.isFile() || file.length() < 1024L * 1024L) return false;
        try (FileInputStream in = new FileInputStream(file)) {
            byte[] h = new byte[4];
            if (in.read(h) != 4) return false;
            boolean little = h[0] == 'I' && h[1] == 'I' && (h[2] & 0xff) == 42 && h[3] == 0;
            boolean big = h[0] == 'M' && h[1] == 'M' && h[2] == 0 && (h[3] & 0xff) == 42;
            return little || big;
        } catch (Exception ignored) { return false; }
    }

    private void downloadCopernicusTile(String tile, File out, int completed, int total) throws Exception {
        Exception last = null;
        for (int attempt = 1; attempt <= 3; attempt++) {
            try {
                downloadCopernicusTileOnce(tile, out, completed, total, attempt);
                if (!isUsableCopernicusTile(out)) throw new IllegalStateException("İndirilen dosya geçerli TIFF değil: " + tile);
                return;
            } catch (Exception e) {
                last = e;
                if (out.exists()) out.delete();
                if (attempt < 3) {
                    sendCopernicusProgress(completed, total, "GLO-30 tekrar deneniyor · " + attempt + "/3 · " + tile);
                    try { Thread.sleep(900L * attempt); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); throw ie; }
                }
            }
        }
        throw last == null ? new IllegalStateException("Copernicus indirilemedi: " + tile) : last;
    }

    private void downloadCopernicusTileOnce(String tile, File out, int completed, int total, int attempt) throws Exception {
        String url = "https://copernicus-dem-30m.s3.amazonaws.com/" + tile + "/" + tile + ".tif";'''
replace_once(old,new,'method')
replace_once('''            conn.setConnectTimeout(15000);
            conn.setReadTimeout(45000);
            conn.setRequestMethod("GET");''','''            conn.setInstanceFollowRedirects(true);
            conn.setConnectTimeout(20000);
            conn.setReadTimeout(90000);
            conn.setUseCaches(false);
            conn.setRequestProperty("User-Agent", "ATLAS-Field/0.25 Android GLO30");
            conn.setRequestProperty("Accept", "image/tiff,application/octet-stream,*/*");
            conn.setRequestMethod("GET");''','http config')
replace_once('''            if (code == 404) throw new IllegalStateException("Copernicus karosu bulunamadı: " + tile);
            if (code < 200 || code >= 300)''','''            if (code == 404) throw new IllegalStateException("Copernicus karosu bulunamadı: " + tile);
            if (code == 403) throw new IllegalStateException("Copernicus erişimi reddedildi (HTTP 403). İnternet/VPN/DNS bağlantısını kontrol edin.");
            if (code == 429) throw new IllegalStateException("Copernicus sunucusu çok fazla istek uyarısı verdi (HTTP 429).");
            if (code < 200 || code >= 300)''','status')
replace_once('byte[] buf = new byte[256 * 1024];','byte[] buf = new byte[128 * 1024];','buffer')
replace_once('sendCopernicusProgress(completed, total, "Copernicus indiriliyor · %" + pct + " · " + tile);','sendCopernicusProgress(completed, total, "GLO-30 %" + pct + " · deneme " + attempt + "/3 · " + tile);','progress')
replace_once('''                }
            }
            if (tmp.length() < 1024L * 1024L)''','''                }
                fos.getFD().sync();
            }
            if (expected > 0 && tmp.length() != expected) throw new IllegalStateException("Copernicus indirmesi eksik: " + tmp.length() + "/" + expected + " bayt");
            if (tmp.length() < 1024L * 1024L)''','sync')
p.write_text(s,encoding='utf-8')

b=Path('ATLAS-v025/app/build.gradle')
t=b.read_text(encoding='utf-8')
t=re.sub(r'versionCode\s+\d+', 'versionCode 25', t)
t=re.sub(r"versionName\s+'[^']*'", "versionName '0.25-glo30-fix'", t)
b.write_text(t,encoding='utf-8')
print('v0.25 GLO-30 patch applied')