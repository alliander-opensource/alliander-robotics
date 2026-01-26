# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
{
  description = "dev environment with debug tools";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python311;
        in
        {
          default = pkgs.mkShell {
            packages = [
              # Python
              (python.withPackages (
                ps: with ps; [
                  debugpy
                  ipython
                  pytest
                ]
              ))
            ];

            shellHook = ''
              echo "dev environment loaded"
            '';
          };
        }
      );
    };
}
