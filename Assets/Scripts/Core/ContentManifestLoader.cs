using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using YOW.Content;

namespace YOW.Core
{
    [Serializable]
    public sealed class ContentManifest
    {
        public string productId;
        public string gameVersion;
        public string manifestVersion;
        public List<PackDescriptor> packs = new();
        public string signature;
    }

    public sealed class ContentManifestLoader : MonoBehaviour
    {
        public ContentManifest Current { get; private set; }

        public Task InitializeAsync()
        {
            Current = new ContentManifest
            {
                productId = "yow-core",
                gameVersion = Application.version,
                manifestVersion = "0.1.0",
                packs = new List<PackDescriptor>()
            };
            return Task.CompletedTask;
        }

        public bool IsPackEnabled(string packId)
        {
            return GetPack(packId) != null;
        }

        public PackDescriptor GetPack(string packId)
        {
            if (Current?.packs == null || string.IsNullOrWhiteSpace(packId))
                return null;

            foreach (var pack in Current.packs)
            {
                if (pack != null && string.Equals(pack.id, packId, StringComparison.OrdinalIgnoreCase))
                    return pack;
            }

            return null;
        }

        public bool NeedsUpdate(string packId, OfflinePackRegistry registry)
        {
            if (registry == null)
                throw new ArgumentNullException(nameof(registry));

            var required = GetPack(packId);
            return required != null && !registry.IsCurrent(required);
        }
    }
}
