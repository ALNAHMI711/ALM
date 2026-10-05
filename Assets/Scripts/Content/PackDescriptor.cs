using System;
using UnityEngine;

namespace YOW.Content
{
    [Serializable]
    public sealed class PackDescriptor
    {
        public string id;
        public string version;
        public string sha256;
        public long sizeBytes;
        public string downloadUrl;
        public bool requiresEntitlement;
    }
}
