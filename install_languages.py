import argostranslate.package
import argostranslate.translate

def install_language_package(from_code, to_code):
    """Install a specific language package for argostranslate"""
    print(f"Installing {from_code} -> {to_code} translation package...")
    
    # Update package index
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    
    # Find the specific package
    package_to_install = next(
        (x for x in available_packages if x.from_code == from_code and x.to_code == to_code),
        None
    )
    
    if package_to_install is None:
        print(f"Package {from_code} -> {to_code} not found!")
        return False
    
    # Download and install the package
    try:
        argostranslate.package.install_from_path(package_to_install.download())
        print(f"Successfully installed {from_code} -> {to_code} package!")
        return True
    except Exception as e:
        print(f"Error installing package: {e}")
        return False

def test_translation(from_code, to_code, test_text="Hello World"):
    """Test if translation works"""
    try:
        translated_text = argostranslate.translate.translate(test_text, from_code, to_code)
        print(f"Test translation: '{test_text}' -> '{translated_text}'")
        return True
    except Exception as e:
        print(f"Translation test failed: {e}")
        return False

if __name__ == "__main__":
    # Install English to French package (as used in app.py)
    from_code = "en"
    to_code = "fr"
    
    if install_language_package(from_code, to_code):
        test_translation(from_code, to_code)
    else:
        print("Failed to install language package!")