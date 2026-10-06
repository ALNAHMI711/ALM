using System;
using System.IO;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using YOW.Core;

namespace YOW.Content
{
    [Serializable]
    public sealed class ContentDownloadTokenResponse
    {
        public string token;
        public int expires_in;
        public string pack_id;
        public string version;
    }

    [Serializable]
    public sealed class ContentDownloadResponse
    {
        public string pack_id;
        public string version;
        public string sha256;
        public long size_bytes;
        public string download_url;
        public int expires_in;
    }

    public sealed class ContentDownloadManager : MonoBehaviour
    {
        [SerializeField] private ContentManifestLoader manifestLoader;
        [SerializeField] private OfflinePackRegistry registry;
        [SerializeField] private string portalBaseUrl = "";
        [SerializeField] private string accountId = "";
        [SerializeField] private string sessionId = "";
        [SerializeField] private int requestTimeoutSeconds = 30;

        public async Task<bool> EnsurePackAsync(string packId)
        {
            var required = manifestLoader?.GetPack(packId);
            if (required == null || registry == null || string.IsNullOrWhiteSpace(portalBaseUrl))
                return false;

            if (!Uri.TryCreate(portalBaseUrl, UriKind.Absolute, out var portalUri) || portalUri.Scheme != Uri.UriSchemeHttps)
                return false;

            if (registry.IsCurrent(required))
                return true;

            if (string.IsNullOrWhiteSpace(accountId) || string.IsNullOrWhiteSpace(sessionId))
                return false;

            var tokenEndpoint = portalBaseUrl.TrimEnd('/') + "/v1/content-download-token";
            var query = "?account_id=" + UnityWebRequest.EscapeURL(accountId)
                + "&device_id=" + UnityWebRequest.EscapeURL(InstallationIdentity.GetOrCreate())
                + "&pack_id=" + UnityWebRequest.EscapeURL(required.id)
                + "&version=" + UnityWebRequest.EscapeURL(required.version);

            var tokenRequest = UnityWebRequest.Post(tokenEndpoint + query, "");
            tokenRequest.timeout = Mathf.Max(1, requestTimeoutSeconds);
            tokenRequest.SetRequestHeader("X-Session-ID", sessionId);

            var tokenOperation = tokenRequest.SendWebRequest();
            while (!tokenOperation.isDone)
                await Task.Yield();

            if (tokenRequest.result != UnityWebRequest.Result.Success)
            {
                tokenRequest.Dispose();
                return false;
            }

            ContentDownloadTokenResponse token;
            try { token = JsonUtility.FromJson<ContentDownloadTokenResponse>(tokenRequest.downloadHandler.text); }
            catch (Exception) { tokenRequest.Dispose(); return false; }
            tokenRequest.Dispose();

            if (token == null || string.IsNullOrWhiteSpace(token.token))
                return false;

            var downloadEndpoint = portalBaseUrl.TrimEnd('/') + "/v1/content-download"
                + query;

            var metadataRequest = UnityWebRequest.Get(downloadEndpoint);
            metadataRequest.timeout = Mathf.Max(1, requestTimeoutSeconds);
            metadataRequest.SetRequestHeader("X-Session-ID", sessionId);
            metadataRequest.SetRequestHeader("X-Content-Download-Token", token.token);

            var metadataOperation = metadataRequest.SendWebRequest();
            while (!metadataOperation.isDone)
                await Task.Yield();

            if (metadataRequest.result != UnityWebRequest.Result.Success)
            {
                metadataRequest.Dispose();
                return false;
            }

            ContentDownloadResponse metadata;
            try { metadata = JsonUtility.FromJson<ContentDownloadResponse>(metadataRequest.downloadHandler.text); }
            catch (Exception) { metadataRequest.Dispose(); return false; }
            metadataRequest.Dispose();

            if (metadata == null || string.IsNullOrWhiteSpace(metadata.download_url)
                || !string.Equals(metadata.pack_id, required.id, StringComparison.OrdinalIgnoreCase)
                || !string.Equals(metadata.version, required.version, StringComparison.OrdinalIgnoreCase)
                || !string.Equals(metadata.sha256, required.sha256, StringComparison.OrdinalIgnoreCase))
                return false;

            if (!Uri.TryCreate(metadata.download_url, UriKind.Absolute, out var signedUri) || signedUri.Scheme != Uri.UriSchemeHttps)
                return false;

            var dataRequest = UnityWebRequest.Get(metadata.download_url);
            dataRequest.timeout = Mathf.Max(1, requestTimeoutSeconds);
            var dataOperation = dataRequest.SendWebRequest();
            while (!dataOperation.isDone)
                await Task.Yield();

            if (dataRequest.result != UnityWebRequest.Result.Success)
            {
                dataRequest.Dispose();
                return false;
            }

            var data = dataRequest.downloadHandler.data;
            dataRequest.Dispose();

            if (data == null || (metadata.size_bytes > 0 && data.LongLength != metadata.size_bytes))
                return false;

            if (!PackIntegrity.VerifySha256(data, metadata.sha256))
                return false;

            var directory = Path.Combine(Application.persistentDataPath, "content");
            Directory.CreateDirectory(directory);
            var path = PackStoragePaths.GetPath(directory, required.id, required.version);
            var tempPath = path + ".partial";

            try
            {
                File.WriteAllBytes(tempPath, data);
                var persisted = File.ReadAllBytes(tempPath);
                if (persisted.LongLength != data.LongLength || !PackIntegrity.VerifySha256(persisted, metadata.sha256))
                {
                    File.Delete(tempPath);
                    return false;
                }

                if (File.Exists(path))
                    File.Delete(path);
                File.Move(tempPath, path);
            }
            catch (IOException)
            {
                if (File.Exists(tempPath))
                    File.Delete(tempPath);
                return false;
            }

            registry.MarkInstalled(new PackDescriptor
            {
                id = required.id,
                version = required.version,
                sha256 = metadata.sha256,
                sizeBytes = data.LongLength
            });
            return true;
        }
    }
}
