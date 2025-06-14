{
  description = "Development environments for various languages";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # Or a specific release
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells = {
          # --- JavaScript/Node.js Environment ---
          javascript = pkgs.mkShell {
            name = "javascript-dev-env";
            buildInputs = [
              pkgs.nodejs_22
              pkgs.nodePackages.npm
              # pkgs.yarn
              # pkgs.nodePackages.typescript
              # pkgs.nodePackages.eslint
              # pkgs.nodePackages.prettier
            ];
            shellHook = ''
              export PATH="$PWD/node_modules/.bin:$PATH"
              echo "Node.js $(node -v) development environment activated (Flake)"
            '';
          };
          node = self.devShells.${system}.javascript;

          # --- C++ Environment ---
          cpp = pkgs.mkShell {
            name = "cpp-dev-env";
            buildInputs = [
              pkgs.gcc
              pkgs.clang
              pkgs.cmake
              pkgs.ninja
              pkgs.gdb
              pkgs.boost
              pkgs.gnumake
              pkgs.ccls
            ];
            shellHook = ''
              export CC=${pkgs.gcc}/bin/gcc
              export CXX=${pkgs.gcc}/bin/g++
              echo "C/C++ development environment activated (Flake)"
              echo "GCC $(gcc --version | head -n1), Clang $(clang --version | head -n1)"
            '';
          };

          # --- Java Environment ---
          java = pkgs.mkShell {
            name = "java-dev-env";
            buildInputs = [
              pkgs.jdk21
              pkgs.maven
              pkgs.gradle
              pkgs.jdt-language-server
              pkgs.spring-boot-cli
            ];
            shellHook = ''
              export JAVA_HOME=${pkgs.jdk21}/lib/openjdk
              export MAVEN_OPTS="-Xmx2G"
              echo "Java development environment activated (Flake)"
              echo "JDK $(java -version 2>&1 | head -n1)"
              echo "Maven $(mvn --version | head -n1)"
            '';
          };

          # --- .NET Environment ---
          dotnet = pkgs.mkShell {
            name = "dotnet-dev-env";
            buildInputs = with pkgs; [
              (dotnetCorePackages.combinePackages [
                dotnetCorePackages.sdk_8_0
                dotnetCorePackages.runtime_8_0
              ])
              omnisharp-roslyn
            ];
            shellHook = ''
              export DOTNET_ROOT="${pkgs.dotnetCorePackages.sdk_8_0}"
              export PATH="$PATH:$HOME/.dotnet/tools"
              export DOTNET_CLI_TELEMETRY_OPTOUT=1
              echo ".NET development environment activated (Flake)"
              echo "$(dotnet --version)"
            '';
          };
          csharp = self.devShells.${system}.dotnet;
          cs = self.devShells.${system}.dotnet;

          # --- Python Environment ---
          python =
            let
              pythonEnv = pkgs.python313;
            in
            pkgs.mkShell {
              name = "python-dev-env";
              buildInputs = [
                pythonEnv
                pythonEnv.pkgs.pip
                pythonEnv.pkgs.venvShellHook
                (pythonEnv.withPackages (ps: with ps; [
                  numpy
                  requests
                  pandas
                ]))
              ];
              venvDir = ".venv-flake";
              postVenvCreation = ''
                pip install --upgrade pip
                echo "Python venv created/updated by Flake."
              '';
              postShellHook = ''
                unset SOURCE_DATE_EPOCH
                echo "Python $(python --version) development environment activated (Flake)"
                echo "Virtual environment available in $venvDir"
              '';
            };
          py = self.devShells.${system}.python;

          # --- Default Shell (Optional, uncomment and set one if desired) ---
          # default = self.devShells.${system}.python;
        };
      }
    );
}
