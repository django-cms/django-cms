/**
 * @author alexander.farkas
 * @version 1.3
 * 
 * @changed by Peter Cicman, added element title support
 */
(function($){
    $.widget('ui.checkBox', {
        _init: function(){
            var that = this, 
			
				opts = this.options,
					
				toggleHover = function(e){
					if(this.disabledStatus){
						return false;
					}
					that.hover = (e.type == 'focus' || e.type == 'mouseenter');
					that._changeStateClassChain();
				};
			if(!this.element.is(':radio,:checkbox')){
				return false;
			}
            this.labels = $([]);
			
            this.checkedStatus = false;
			this.disabledStatus = false;
			this.hoverStatus = false;
            
            this.radio = (this.element.is(':radio'));
			
			this.visualElement = $('<span />')
				.addClass(this.radio ? 'ui-radio' : 'ui-checkbox')
				.bind('mouseenter.checkBox mouseleave.checkBox', toggleHover)
				.bind('click.checkBox', function(e){
					that.element[0].click();
					//that.element.trigger('click');
					return false;
				});		
            
			// element title suport added by Peter Cicman
			if (this.element.attr("title")) {
				this.visualElement.attr("title", this.element.attr("title"));
			}
			
			// class name copy added by Peter Cicman - add all classes names 
			// form original input to new element, but only the ones, which are
			// starting with `copy-`, but remove `copy-` from it.
			classNames = this.element.attr("class").match(/copy-[a-z0-9A-Z_]+/g);
			for (var i=0; i < classNames.length; i++) {
				this.visualElement.addClass(classNames[i].replace(/^copy-/, ''));
			}
			
			
            if (opts.replaceInput) {
				this.element
					.addClass('ui-helper-hidden-accessible')
					.after(this.visualElement[0])
					.bind('usermode', function(e){
	                    (e.enabled &&
	                        that.destroy.call(that, true));
	                });
            }
			
			this.element
				.bind('click.checkBox', $.bind(this, this.reflectUI))
				.bind('focus.checkBox blur.checkBox', toggleHover);
				
			if(opts.addLabel){
				//ToDo: Add Closest Ancestor
				this.labels = $('label[for=' + this.element.attr('id') + ']')
					.bind('mouseenter.checkBox mouseleave.checkBox', toggleHover);
			}
			
            this.reflectUI({type: 'initialReflect'});
        },
		_changeStateClassChain: function(){
			var stateClass = (this.checkedStatus) ? '-checked' : '',
				baseClass = 'ui-'+((this.radio) ? 'radio' : 'checkbox')+'-state';
			
			stateClass += (this.disabledStatus) ? '-disabled' : '';
			stateClass += (this.hover) ? '-hover' : '';
				
			if(stateClass){
				stateClass = baseClass + stateClass;
			}
			
			function switchStateClass(){
				var classes = this.className.split(' '),
					found = false;
				$.each(classes, function(i, classN){
					if(classN.indexOf(baseClass) === 0){
						found = true;
						classes[i] = stateClass;
						return false;
					} 
				});
				if(!found){
					classes.push(stateClass);
				}
				
				this.className = classes.join(' ');
			}
			
			this.labels.each(switchStateClass);
			this.visualElement.each(switchStateClass);
		},
        destroy: function(onlyCss){
            this.element.removeClass('ui-helper-hidden-accessible');
			this.visualElement.addClass('ui-helper-hidden');
            if (!onlyCss) {
                var o = this.options;
                this.element.unbind('.checkBox');
				this.visualElement.remove();
                this.labels
					.unbind('.checkBox')
					.removeClass('ui-state-hover ui-state-checked ui-state-disabled');
            }
        },
		
        disable: function(){
            this.element[0].disabled = true;
            this.reflectUI({type: 'manuallyDisabled'});
        },
		
        enable: function(){
            this.element[0].disabled = false;
            this.reflectUI({type: 'manuallyenabled'});
        },
		
        toggle: function(e){
            this.changeCheckStatus((this.element.is(':checked')) ? false : true, e);
        },
		
        changeCheckStatus: function(status, e){
            if(e && e.type == 'click' && this.element[0].disabled){
				return false;
			}
			this.element.attr({'checked': status});
            this.reflectUI(e || {
                type: 'changeCheckStatus'
            });
        },
		
        propagate: function(n, e, _noGroupReflect){
			if(!e || e.type != 'initialReflect'){
				if (this.radio && !_noGroupReflect) {
					//dynamic
	                $(document.getElementsByName(this.element.attr('name')))
						.checkBox('reflectUI', e, true);
	            }
	            return this._trigger(n, e, {
	                options: this.options,
	                checked: this.checkedStatus,
	                labels: this.labels,
					disabled: this.disabledStatus
	            });
			}
        },
		
        reflectUI: function(elm, e){
            var oldChecked = this.checkedStatus, 
				oldDisabledStatus = this.disabledStatus;
            e = e ||
            	elm;
					
			this.disabledStatus = this.element.is(':disabled');
			this.checkedStatus = this.element.is(':checked');
			
			if (this.disabledStatus != oldDisabledStatus || this.checkedStatus !== oldChecked) {
				this._changeStateClassChain();
				
				(this.disabledStatus != oldDisabledStatus &&
					this.propagate('disabledChange', e));
				
				(this.checkedStatus !== oldChecked &&
					this.propagate('change', e));
			}
            
        }
    });
    $.ui.checkBox.defaults = {
        replaceInput: true,
		addLabel: true
    };
    
})(jQuery);
