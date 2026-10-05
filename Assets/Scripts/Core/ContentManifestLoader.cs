using System;
using System.Threading.Tasks;
using UnityEngine;

namespace YOW.Core
{
    [Serializable]
    public sealed class ContentManifest
    {
        public string gameVersion;
        public string manifestVersion;
        public string[] packs;
        public string signature;
    }

    public sealed class ContentManifestLoader : MonoBehaviour
    {
        public ContentManifest Current { get; private set; }

        public Task InitializeAsync()
        {
            // Production implementation will fetch a signed manifest from the portal.
            // Offline builds can use the last verified cached manifest.
            Current = new ContentManifest
            {
                gameVersion = Application.version,
                manifestVersion = "0.1.0",
                packs = Array.Empty<string>()
            };
            return Task.CompletedTask;
        }

        public bool IsPackEnabled(string packId)
        {
            if (Current?.packs == null) return false;
            foreach (var pack in Current.packs)
                if (string.Equals(pack, packId, StringComparison.OrdinalIgnoreCase))
                    return true;
            return false;
        }
    }
}
