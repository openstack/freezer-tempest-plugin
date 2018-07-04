# install_freezer_tempest_plugin
function install_freezer_tempest_plugin {
    setup_dev_lib "freezer-tempest-plugin"
}

if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            echo_summary "Installing freezer-tempest-plugin"
            install_freezer_tempest_plugin
            ;;
    esac
fi
