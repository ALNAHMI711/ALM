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

        private void Save()
        {
            var snapshot = new Snapshot { packs = new List<InstalledPack>(installed.Values) };
            PlayerPrefs.SetString(PlayerPrefsKey, JsonUtility.ToJson(snapshot));
            PlayerPrefs.Save();
        }
    }
}
