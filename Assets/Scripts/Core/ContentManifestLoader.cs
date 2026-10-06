using System;
using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
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

    [Serializable]
    internal sealed class PortalContentManifest
    {
        public string product_id;
        public string productId;
        public List<PortalPack> packs = new();
    }

    [Serializable]
    internal sealed class PortalPack
    {
        public string pack_id;
        public string id;
        public string version;
        public string platform;
        public string sha256;
        public long size_bytes;
        public long sizeBytes;
        public string required_core_version;
        public string requiredCoreVersion;
    }

    public sealed class ContentManifestLoader : MonoBehaviour
    {
        [SerializeField] private string manifestUrl = "";
        [SerializeField] private int requestTimeoutSeconds = 10;

        private string sessionId;
        private string accountId;

        public ContentManifest Current { get; private set; }
        public bool LoadedFromServer { get; private set; }

        public void ConfigureAuthentication(string account, string session)
        {
            accountId = account ?? string.Empty;
            sessionId = session ?? string.Empty;
        }

        public async Task InitializeAsync()
        {
            if (string.IsNullOrWhiteSpace(manifestUrl))
            {
                SetEmptyManifest();
                return;
            }

            var request = UnityWebRequest.Get(manifestUrl);
            if (!string.IsNullOrWhiteSpace(accountId))
                request.SetRequestHeader("X-Account-ID", accountId);
            if (!string.IsNullOrWhiteSpace(sessionId))
                request.SetRequestHeader("X-Session-ID", sessionId);
            request.timeout = Mathf.Max(1, requestTimeoutSeconds);
            var operation = request.SendWebRequest();
            while (!operation.isDone)
                await Task.Yield();

            if (request.result != UnityWebRequest.Result.Success)
            {
                SetEmptyManifest();
                return;
            }

            try
            {
                var payload = JsonUtility.FromJson<PortalContentManifest>(request.downloadHandler.text);
                Current = Convert(payload);
                LoadedFromServer = true;
            }
            catch (Exception)
            {
                SetEmptyManifest();
            }
            finally
            {
                request.Dispose();
            }
        }

        public bool IsPackEnabled(string packId) => GetPack(packId) != null;

        public PackDescriptor GetPack(string packId)
        {
            if (Current?.packs == null || string.IsNullOrWhiteSpace(packId))
                return null;

            foreach (var pack in Current.packs)
                if (pack != null && string.Equals(pack.id, packId, StringComparison.OrdinalIgnoreCase))
                    return pack;

            return null;
        }

        public bool NeedsUpdate(string packId, OfflinePackRegistry registry)
        {
            if (registry == null)
                throw new ArgumentNullException(nameof(registry));

            var required = GetPack(packId);
            return required != null && !registry.IsCurrent(required);
        }

        private void SetEmptyManifest()
        {
            LoadedFromServer = false;
            Current = new ContentManifest
            {
                productId = "yow-core",
                gameVersion = Application.version,
                manifestVersion = "0.0.0",
                packs = new List<PackDescriptor>()
            };
        }

        private static ContentManifest Convert(PortalContentManifest payload)
        {
            if (payload == null)
                throw new InvalidOperationException("empty manifest");

            var result = new ContentManifest
            {
                productId = string.IsNullOrWhiteSpace(payload.product_id) ? payload.productId : payload.product_id,
                gameVersion = Application.version,
                manifestVersion = "server",
                packs = new List<PackDescriptor>()
            };

            if (payload.packs == null)
                return result;

            foreach (var source in payload.packs)
            {
                if (source == null || string.IsNullOrWhiteSpace(source.version))
                    continue;

                result.packs.Add(new PackDescriptor
                {
                    id = string.IsNullOrWhiteSpace(source.pack_id) ? source.id : source.pack_id,
                    version = source.version,
                    platform = source.platform,
                    sha256 = source.sha256,
                    sizeBytes = source.size_bytes > 0 ? source.size_bytes : source.sizeBytes,
                    requiredCoreVersion = string.IsNullOrWhiteSpace(source.required_core_version)
                        ? source.requiredCoreVersion
                        : source.required_core_version,
                    requiresEntitlement = true
                });
            }

            return result;
        }
    }
}
