# iOS Podfile Fix for Firebase
# Replace your ios/Podfile with this content

platform :ios, '12.0'

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  # Flutter pods
  pod 'Flutter', :path => '../Flutter'
  
  # Firebase pods
  pod 'Firebase/Core'
  pod 'Firebase/Messaging'
  
  # Fix for Firebase modular headers
  pod 'Firebase', :modular_headers => true
  pod 'FirebaseCore', :modular_headers => true
  pod 'FirebaseMessaging', :modular_headers => true
  
  target 'RunnerTests' do
    inherit! :search_paths
  end
end

# Post install script to fix Firebase headers
post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
    
    # Fix Firebase modular headers
    target.build_configurations.each do |config|
      config.build_settings['CLANG_ALLOW_NON_MODULAR_INCLUDES_IN_FRAMEWORK_MODULES'] = 'YES'
      config.build_settings['DEFINES_MODULE'] = 'YES'
    end
  end
end
