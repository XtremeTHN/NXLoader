{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    python3 = (pkgs.python313.withPackages (ps: with ps; [
      pygobject3
      pycairo
      pyusb
    ]));

    nativeBuildInputs = with pkgs; [
      python3
      desktop-file-utils
      blueprint-compiler
      meson
      ninja
      pkg-config
      wrapGAppsHook4
    ];
    buildInputs = with pkgs; [
      gtk4
      libadwaita
      libgudev
    ];
  in {
    
    devShells.${system}.default = pkgs.mkShell {
      inherit nativeBuildInputs buildInputs;
      packages = with pkgs; [
        python3.pkgs.pygobject-stubs
      ];
    };

    packages.${system}.default = pkgs.stdenv.mkDerivation {
      name = "nxloader";
      versin = "0.1";
      src = ./.;

      inherit nativeBuildInputs buildInputs;
    };
  };
}
