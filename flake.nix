{
  description = "My Dev Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/25.05";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = with pkgs; [
        which
        gcc
        cmake
        git
        subversion
        python312
        python312Packages.numpy
        python312Packages.setuptools
        python312Packages.wheel
        python312Packages.pip
        python312Packages.torch
        python312Packages.torchaudio
        python312Packages.transformers 
        python312Packages.posix_ipc
        python312Packages.scipy
      ];

      shellHook = ''
        source ./venv/bin/activate
      '';
    };
  };
}
