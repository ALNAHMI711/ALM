using System;
using UnityEngine;

namespace YOW.Content
{
    [Serializable]
    public sealed class PackDescriptor
    {
        public string id;
        public string version;
        public string platform;
        public string sha256;
        public long sizeBytes;
        public string requiredCoreVersion;
        public bool requiresEntitlement;

        public bool Matches(string packId, string requiredVersion, string requiredSha256)
        {
            return string.Equals(id, packId, StringComparison.OrdinalIgnoreCase)
                && string.Equals(version, requiredVersion, StringComparison.OrdinalIgnoreCase)
                && string.Equals(sha256, requiredSha256, StringComparison.OrdinalIgnoreCase);
        }
    }
}
