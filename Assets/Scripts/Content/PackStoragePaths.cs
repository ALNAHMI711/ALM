using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace YOW.Content
{
    public static class PackStoragePaths
    {
        public static string GetPath(string root, string packId, string version)
        {
            if (string.IsNullOrWhiteSpace(root) || string.IsNullOrWhiteSpace(packId) || string.IsNullOrWhiteSpace(version))
                throw new ArgumentException("pack storage identity required");

            using var sha = SHA256.Create();
            var key = Encoding.UTF8.GetBytes(packId + ":" + version);
            var hash = Convert.ToHexString(sha.ComputeHash(key)).ToLowerInvariant();
            return Path.Combine(root, hash + ".pack");
        }
    }
}
