using System;
using System.Collections.Generic;
using UnityEngine;

namespace YOW.Content
{
    [Serializable]
    public sealed class InstalledPack
    {
        public string id;
        public string version;
        public string sha256;
        public long sizeBytes;
    }

    public sealed class OfflinePackRegistry : MonoBehaviour
    {
        private const string PlayerPrefsKey = "YOW.InstalledPacks";
        private readonly Dictionary<string, InstalledPack> installed = new();

        [Serializable]
        private sealed class Snapshot
        {
            public List<InstalledPack> packs = new();
        }

        private void Awake()
        {
            Load();
        }

        public bool IsInstalled(string packId) => !string.IsNullOrWhiteSpace(packId) && installed.ContainsKey(packId);

        public bool IsCurrent(PackDescriptor required)
        {
            if (required == null || !installed.TryGetValue(required.id, out var current))
                return false;

            return current != null
                && string.Equals(current.version, required.version, StringComparison.OrdinalIgnoreCase)
                && string.Equals(current.sha256, required.sha256, StringComparison.OrdinalIgnoreCase)
                && (required.sizeBytes <= 0 || current.sizeBytes == required.sizeBytes);
        }

        public InstalledPack Get(string packId)
        {
            installed.TryGetValue(packId, out var pack);
            return pack;
        }

        public void MarkInstalled(PackDescriptor pack)
        {
            if (pack == null || string.IsNullOrWhiteSpace(pack.id))
                return;

            installed[pack.id] = new InstalledPack
            {
                id = pack.id,
                version = pack.version,
                sha256 = pack.sha256,
                sizeBytes = pack.sizeBytes
            };
            Save();
        }

        public void MarkInstalled(string packId)
        {
            if (string.IsNullOrWhiteSpace(packId))
                return;

            installed[packId] = new InstalledPack { id = packId };
            Save();
        }

        public void Remove(string packId)
        {
            if (!string.IsNullOrWhiteSpace(packId))
            {
                installed.Remove(packId);
                Save();
            }
        }

        public void Revalidate(string contentDirectory)
        {
            var invalid = new List<string>();
            foreach (var pair in installed)
            {
                var pack = pair.Value;
                if (pack == null || string.IsNullOrWhiteSpace(pack.version) || string.IsNullOrWhiteSpace(pack.sha256))
                {
                    invalid.Add(pair.Key);
                    continue;
                }

                var path = System.IO.Path.Combine(contentDirectory, pack.id + "-" + pack.version + ".pack");
                if (!System.IO.File.Exists(path))
                {
                    invalid.Add(pair.Key);
                    continue;
                }

                try
                {
                    var data = System.IO.File.ReadAllBytes(path);
                    if ((pack.sizeBytes > 0 && data.LongLength != pack.sizeBytes) || !PackIntegrity.VerifySha256(data, pack.sha256))
                        invalid.Add(pair.Key);
                }
                catch (IOException)
                {
                    invalid.Add(pair.Key);
                }
            }

            foreach (var packId in invalid)
                installed.Remove(packId);

            if (invalid.Count > 0)
                Save();
        }

        private void Load()
        {
            installed.Clear();
            var json = PlayerPrefs.GetString(PlayerPrefsKey, "");
            if (string.IsNullOrWhiteSpace(json))
                return;

            try
            {
                var snapshot = JsonUtility.FromJson<Snapshot>(json);
                if (snapshot?.packs == null)
                    return;

                foreach (var pack in snapshot.packs)
                {
                    if (pack != null && !string.IsNullOrWhiteSpace(pack.id))
                        installed[pack.id] = pack;
                }
            }
            catch (Exception)
            {
                installed.Clear();
            }
        }

        public string ContentDirectory => System.IO.Path.Combine(Application.persistentDataPath, "content");

        private void Save()
        {
            var snapshot = new Snapshot { packs = new List<InstalledPack>(installed.Values) };
            PlayerPrefs.SetString(PlayerPrefsKey, JsonUtility.ToJson(snapshot));
            PlayerPrefs.Save();
        }
    }
}
