{
  description = "Dev environment with basic tools";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }: {
    devShells.default = nixpkgs.legacyPackages.x86_64-linux.mkShell {
      buildInputs = [
        nixpkgs.legacyPackages.x86_64-linux.curl
        nixpkgs.legacyPackages.x86_64-linux.ca-certificates
        nixpkgs.legacyPackages.x86_64-linux.wget
        nixpkgs.legacyPackages.x86_64-linux.gnupg
        nixpkgs.legacyPackages.x86_64-linux.tmux
      ];
    };
  };
}
