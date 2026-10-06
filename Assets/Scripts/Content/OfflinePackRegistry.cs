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
    }

    public sealed class OfflinePackRegistry : MonoBehaviour
    {
        private readonly Dictionary<string, InstalledPack> installed = new();

        public bool IsInstalled(string packId) => installed.ContainsKey(packId);

        public bool IsCurrent(PackDescriptor required)
        {
            if (required == null || !installed.TryGetValue(required.id, out var current))
                return false;

            return current != null
                && string.Equals(current.version, required.version, StringComparison.OrdinalIgnoreCase)
                && string.Equals(current.sha256, required.sha256, StringComparison.OrdinalIgnoreCase);
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
                sha256 = pack.sha256
            };
        }

        public void MarkInstalled(string packId)
        {
            if (!string.IsNullOrWhiteSpace(packId))
                installed[packId] = new InstalledPack { id = packId };
        }

        public void Remove(string packId)
        {
            if (!string.IsNullOrWhiteSpace(packId))
                installed.Remove(packId);
        }
    }
}
